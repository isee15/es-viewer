# coding: utf-8
"""
A PyQt application to view and manage Elasticsearch with full CRUD operations,
HTTPS support, and corrected copy-paste functionality.
Author: isee15
Date: 2025-10-01
"""
import sys
import json
import os
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth
import urllib3

# When choosing not to verify SSL certs, requests will print warnings. We disable them here.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTreeView, QSplitter,
    QStatusBar, QMessageBox, QCheckBox, QFormLayout, QTabWidget, QMenu
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont, QKeySequence, QAction, QShortcut
from PyQt6.QtCore import Qt

# --- Config File Path ---
CONFIG_FILE = Path.home() / ".es_viewer_config.json"

# ==============================================================================
#  Business Logic Layer: Custom Elasticsearch Client
# ==============================================================================

class SimpleEsClientError(Exception):
    """Custom exception for client-side errors."""
    pass

class SimpleEsClient:
    """
    A minimal, handwritten Elasticsearch Python client.
    Supports HTTPS and SSL certificate verification control.
    """
    def __init__(self, base_url: str, auth: tuple = None, verify_ssl: bool = True):
        if base_url.endswith('/'): self.base_url = base_url[:-1]
        else: self.base_url = base_url
        self.auth = HTTPBasicAuth(auth[0], auth[1]) if auth else None
        self.headers = {"Content-Type": "application/json"}
        self.verify_ssl = verify_ssl

    def _make_request(self, method, endpoint, **kwargs):
        """Generic request handler."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(
                method=method, url=url, auth=self.auth, headers=self.headers,
                timeout=10, verify=self.verify_ssl, **kwargs
            )
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                 return {"acknowledged": True, "status": response.status_code, "operation": method}
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_details = f"HTTP Error: {e.response.status_code} {e.response.reason}"
            try:
                es_error_body = e.response.json()
                error_details += f"\nDetails: {json.dumps(es_error_body)}"
            except json.JSONDecodeError: error_details += f"\nResponse Body: {e.response.text}"
            raise SimpleEsClientError(error_details) from e
        except requests.exceptions.SSLError as e:
            raise SimpleEsClientError(f"SSL Error: Could not verify certificate. Try unchecking 'Verify SSL Certificate'.\nDetails: {e}") from e
        except requests.exceptions.RequestException as e:
            raise SimpleEsClientError(f"Connection failed: {e}") from e

    def info(self): return self._make_request("GET", "")
    def search(self, index: str, query: dict): return self._make_request("POST", f"{index}/_search", json=query)
    def get_document(self, index: str, doc_id: str): return self._make_request("GET", f"{index}/_doc/{doc_id}")
    def index_document(self, index: str, document: dict, doc_id: str = None):
        if doc_id: return self._make_request("PUT", f"{index}/_doc/{doc_id}", json=document)
        else: return self._make_request("POST", f"{index}/_doc", json=document)
    def update_document(self, index: str, doc_id: str, payload: dict): return self._make_request("POST", f"{index}/_update/{doc_id}", json=payload)
    def delete_document(self, index: str, doc_id: str): return self._make_request("DELETE", f"{index}/_doc/{doc_id}")

# ==============================================================================
#  UI Presentation Layer: PyQt Application
# ==============================================================================

class ElasticsearchViewer(QMainWindow):
    """
    A PyQt viewer for Elasticsearch with full CRUD, HTTPS, and corrected copy-paste support.
    """
    def __init__(self):
        super().__init__()
        self.es_client = None
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initializes the user interface."""
        self.setWindowTitle('ES Viewer v1.0')
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        connection_group = QWidget()
        connection_layout = QFormLayout(connection_group)
        connection_layout.setContentsMargins(0, 5, 0, 5)
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.index_input = QLineEdit()
        connection_layout.addRow('Host:', self.host_input)
        connection_layout.addRow('Port:', self.port_input)
        connection_layout.addRow('Index:', self.index_input)
        
        https_layout = QHBoxLayout()
        self.https_checkbox = QCheckBox('Use HTTPS')
        self.verify_ssl_checkbox = QCheckBox('Verify SSL Certificate')
        https_layout.addWidget(self.https_checkbox)
        https_layout.addWidget(self.verify_ssl_checkbox)
        connection_layout.addRow(https_layout)
        
        self.auth_checkbox = QCheckBox('Enable Authentication')
        connection_layout.addRow(self.auth_checkbox)
        self.user_label = QLabel('Username:')
        self.user_input = QLineEdit()
        self.pass_label = QLabel('Password:')
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        connection_layout.addRow(self.user_label, self.user_input)
        connection_layout.addRow(self.pass_label, self.pass_input)
        self.user_label.hide(); self.user_input.hide()
        self.pass_label.hide(); self.pass_input.hide()

        self.auth_checkbox.toggled.connect(self.toggle_auth_fields)
        self.https_checkbox.toggled.connect(self.toggle_ssl_verify_option)

        main_layout.addWidget(connection_group)
        
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.tabs = QTabWidget()
        self.tab_search = QWidget()
        self.tab_crud = QWidget()
        self.tabs.addTab(self.tab_search, "Search")
        self.tabs.addTab(self.tab_crud, "Document CRUD")
        
        search_layout = QVBoxLayout(self.tab_search)
        search_layout.setContentsMargins(0, 5, 0, 0)
        search_layout.addWidget(QLabel("Search Request Body (Query DSL JSON):"))
        self.query_input = QTextEdit()
        self.query_input.setFont(QFont("Courier", 10))
        search_layout.addWidget(self.query_input)
        self.execute_search_button = QPushButton('Execute Search')
        self.execute_search_button.clicked.connect(self.execute_search)
        search_layout.addWidget(self.execute_search_button)

        crud_layout = QVBoxLayout(self.tab_crud)
        crud_layout.setContentsMargins(0, 5, 0, 0)
        crud_form_layout = QFormLayout()
        self.doc_id_input = QLineEdit()
        self.doc_id_input.setPlaceholderText("ID is required for Get, Index(PUT), Update, Delete")
        crud_form_layout.addRow("Document ID:", self.doc_id_input)
        crud_layout.addLayout(crud_form_layout)
        crud_layout.addWidget(QLabel("Document Body / Update Payload:"))
        self.doc_body_input = QTextEdit()
        self.doc_body_input.setFont(QFont("Courier", 10))
        crud_layout.addWidget(self.doc_body_input)
        button_layout = QHBoxLayout()
        self.get_button = QPushButton("Get")
        self.index_button = QPushButton("Index/Create")
        self.update_button = QPushButton("Update")
        self.delete_button = QPushButton("Delete")
        button_layout.addWidget(self.get_button); button_layout.addWidget(self.index_button)
        button_layout.addWidget(self.update_button); button_layout.addWidget(self.delete_button)
        crud_layout.addLayout(button_layout)
        
        self.get_button.clicked.connect(self.execute_get)
        self.index_button.clicked.connect(self.execute_index)
        self.update_button.clicked.connect(self.execute_update)
        self.delete_button.clicked.connect(self.execute_delete)

        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 5, 0, 0)
        results_layout.addWidget(QLabel("Results:"))
        self.results_tree = QTreeView()
        results_layout.addWidget(self.results_tree)
        
        main_splitter.addWidget(self.tabs)
        main_splitter.addWidget(results_widget)
        main_splitter.setSizes([350, 450])
        main_layout.addWidget(main_splitter)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.setup_copy_functionality()

    # --- Copy-Paste Functionality ---
    def setup_copy_functionality(self):
        self.results_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_tree.customContextMenuRequested.connect(self.open_tree_context_menu)
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self.results_tree)
        copy_shortcut.activated.connect(self.copy_selection_to_clipboard)
        
    def open_tree_context_menu(self, position):
        index = self.results_tree.indexAt(position)
        if index.isValid():
            menu = QMenu(); copy_action = QAction("Copy", self)
            copy_action.triggered.connect(self.copy_selection_to_clipboard); menu.addAction(copy_action)
            menu.exec(self.results_tree.viewport().mapToGlobal(position))

    def copy_selection_to_clipboard(self):
        """
        CORRECTED: Copies the key-value pair of the selected row to the clipboard.
        """
        selected_indexes = self.results_tree.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        # Get the index of the first selected cell to identify the row and parent
        selected_index = selected_indexes[0]
        model = self.results_tree.model()

        # Get the index for the key (column 0) of the selected row
        key_index = model.index(selected_index.row(), 0, selected_index.parent())
        key_text = model.data(key_index, Qt.ItemDataRole.DisplayRole)

        # Get the index for the value (column 1) of the selected row
        value_index = model.index(selected_index.row(), 1, selected_index.parent())
        value_text = model.data(value_index, Qt.ItemDataRole.DisplayRole)

        # Determine the final text to copy
        if value_text:
            # If there is a value, copy the full key-value pair
            text_to_copy = f"{key_text}: {value_text}"
        else:
            # If there's no value (it's a parent node), just copy the key
            text_to_copy = key_text
        
        if text_to_copy:
            QApplication.clipboard().setText(text_to_copy)
            self.status_bar.showMessage(f"Copied: '{text_to_copy}'", 3000)
            
    # --- Client and Settings Methods ---
    def _get_client(self):
        host = self.host_input.text().strip(); port = self.port_input.text().strip()
        if not host or not port:
            QMessageBox.warning(self, 'Input Error', 'Host and Port cannot be empty.')
            return None
        scheme = "https" if self.https_checkbox.isChecked() else "http"
        verify_ssl = self.verify_ssl_checkbox.isChecked()
        base_url = f"{scheme}://{host}:{port}"
        auth_tuple = None
        if self.auth_checkbox.isChecked():
            auth_tuple = (self.user_input.text(), self.pass_input.text())
        return SimpleEsClient(base_url=base_url, auth=auth_tuple, verify_ssl=verify_ssl)
        
    def save_settings(self):
        settings = {"host": self.host_input.text(), "port": self.port_input.text(), "index": self.index_input.text(), "https_enabled": self.https_checkbox.isChecked(), "verify_ssl": self.verify_ssl_checkbox.isChecked(), "auth_enabled": self.auth_checkbox.isChecked(), "username": self.user_input.text(), "password": self.pass_input.text(), "query": self.query_input.toPlainText()}
        try:
            with open(CONFIG_FILE, 'w') as f: json.dump(settings, f, indent=4)
        except IOError: pass

    def load_settings(self):
        default_query = {"query": {"match_all": {}}, "size": 10}
        default_update = {"doc": {"field_name": "new_value"}}
        if not os.path.exists(CONFIG_FILE):
            self.host_input.setText("localhost"); self.port_input.setText("9200"); self.index_input.setText("my-index")
            self.query_input.setText(json.dumps(default_query, indent=2))
            self.doc_body_input.setText(json.dumps(default_update, indent=2))
            self.verify_ssl_checkbox.setChecked(True)
            self.toggle_ssl_verify_option(self.https_checkbox.isChecked())
            return
        try:
            with open(CONFIG_FILE, 'r') as f: settings = json.load(f)
            self.host_input.setText(settings.get("host", "localhost")); self.port_input.setText(settings.get("port", "9200")); self.index_input.setText(settings.get("index", ""))
            self.https_checkbox.setChecked(settings.get("https_enabled", False)); self.verify_ssl_checkbox.setChecked(settings.get("verify_ssl", True))
            self.toggle_ssl_verify_option(self.https_checkbox.isChecked())
            self.auth_checkbox.setChecked(settings.get("auth_enabled", False))
            self.user_input.setText(settings.get("username", "")); self.pass_input.setText(settings.get("password", ""))
            self.query_input.setText(settings.get("query", json.dumps(default_query, indent=2)))
            self.doc_body_input.setText(json.dumps(default_update, indent=2))
        except (IOError, json.JSONDecodeError, KeyError): pass

    # --- Slots and Helper Methods ---
    def toggle_ssl_verify_option(self, checked):
        self.verify_ssl_checkbox.setVisible(checked)
    def toggle_auth_fields(self, checked):
        self.user_label.setVisible(checked); self.user_input.setVisible(checked)
        self.pass_label.setVisible(checked); self.pass_input.setVisible(checked)
    def execute_search(self):
        client = self._get_client(); index_name = self.index_input.text().strip()
        if not client or not index_name: QMessageBox.warning(self, 'Input Error', 'Host, Port, and Index are required.'); return
        try:
            query_json = json.loads(self.query_input.toPlainText())
            self.status_bar.showMessage(f'Executing search on index "{index_name}"...'); QApplication.processEvents()
            response = client.search(index=index_name, query=query_json)
            self.populate_tree(response); self.status_bar.showMessage('Search successful. Settings saved.', 5000); self.save_settings()
        except json.JSONDecodeError as e: QMessageBox.critical(self, 'JSON Error', f'Invalid JSON in query box:\n{e}')
        except SimpleEsClientError as e: QMessageBox.critical(self, 'Client Error', str(e))
    def execute_get(self):
        client = self._get_client(); index = self.index_input.text().strip(); doc_id = self.doc_id_input.text().strip()
        if not all([client, index, doc_id]): QMessageBox.warning(self, 'Input Error', 'Host, Port, Index and Document ID are required.'); return
        try:
            self.status_bar.showMessage(f"Getting document '{doc_id}'..."); response = client.get_document(index, doc_id)
            self.populate_tree(response); self.doc_body_input.setText(json.dumps(response.get("_source", {}), indent=2))
            self.status_bar.showMessage(f"Get document '{doc_id}' successful.", 5000)
        except SimpleEsClientError as e: QMessageBox.critical(self, 'Client Error', str(e))
    def execute_index(self):
        client = self._get_client(); index = self.index_input.text().strip(); doc_id = self.doc_id_input.text().strip() or None
        if not all([client, index]): QMessageBox.warning(self, 'Input Error', 'Host, Port, and Index are required.'); return
        try:
            doc_body = json.loads(self.doc_body_input.toPlainText())
            self.status_bar.showMessage(f"Indexing document in '{index}'..."); response = client.index_document(index, doc_body, doc_id)
            self.populate_tree(response)
            if response.get("_id"): self.doc_id_input.setText(response["_id"])
            self.status_bar.showMessage(f"Index operation successful.", 5000)
        except json.JSONDecodeError as e: QMessageBox.critical(self, 'JSON Error', f'Invalid JSON in document body:\n{e}')
        except SimpleEsClientError as e: QMessageBox.critical(self, 'Client Error', str(e))
    def execute_update(self):
        client = self._get_client(); index = self.index_input.text().strip(); doc_id = self.doc_id_input.text().strip()
        if not all([client, index, doc_id]): QMessageBox.warning(self, 'Input Error', 'Host, Port, Index and Document ID are required.'); return
        try:
            payload = json.loads(self.doc_body_input.toPlainText())
            self.status_bar.showMessage(f"Updating document '{doc_id}'..."); response = client.update_document(index, doc_id, payload)
            self.populate_tree(response); self.status_bar.showMessage(f"Update operation successful.", 5000)
        except json.JSONDecodeError as e: QMessageBox.critical(self, 'JSON Error', f'Invalid JSON in update payload:\n{e}')
        except SimpleEsClientError as e: QMessageBox.critical(self, 'Client Error', str(e))
    def execute_delete(self):
        client = self._get_client(); index = self.index_input.text().strip(); doc_id = self.doc_id_input.text().strip()
        if not all([client, index, doc_id]): QMessageBox.warning(self, 'Input Error', 'Host, Port, Index and Document ID are required.'); return
        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete document '{doc_id}' from index '{index}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.No: return
        try:
            self.status_bar.showMessage(f"Deleting document '{doc_id}'..."); response = client.delete_document(index, doc_id)
            self.populate_tree(response); self.status_bar.showMessage(f"Delete operation successful.", 5000)
            self.doc_id_input.clear(); self.doc_body_input.clear()
        except SimpleEsClientError as e: QMessageBox.critical(self, 'Client Error', str(e))
    def populate_tree(self, data):
        model = QStandardItemModel(); model.setHorizontalHeaderLabels(['Key', 'Value'])
        self.results_tree.setModel(model); root_item = model.invisibleRootItem()
        self._populate_tree_model(data, root_item); self.results_tree.expandToDepth(2)
    def _populate_tree_model(self, data, parent_item):
        if isinstance(data, dict):
            for key, value in data.items():
                key_item = QStandardItem(str(key)); key_item.setEditable(False)
                value_item = QStandardItem(); value_item.setEditable(False)
                parent_item.appendRow([key_item, value_item])
                if isinstance(value, (dict, list)): self._populate_tree_model(value, key_item)
                else: value_item.setText(str(value))
        elif isinstance(data, list):
            for index, value in enumerate(data):
                index_item = QStandardItem(f"[{index}]"); index_item.setEditable(False)
                value_item = QStandardItem(); value_item.setEditable(False)
                parent_item.appendRow([index_item, value_item])
                if isinstance(value, (dict, list)): self._populate_tree_model(value, index_item)
                else: value_item.setText(str(value))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ElasticsearchViewer()
    viewer.show()
    sys.exit(app.exec())