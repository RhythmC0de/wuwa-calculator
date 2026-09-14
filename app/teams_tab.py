"""Team-management tab with UI-only state ready for persistence wiring."""

from PySide6.QtCore import QStringListModel
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QListView, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.components import Card, TitleLabel
from app.styles import apply_glow
from storage.team_storage import load_teams, save_teams


class TeamsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        sidebar = Card()
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 16, 16, 16)
        side_layout.addWidget(TitleLabel("Teams"))
        self.teams = load_teams()
        self.selected_team_index = -1
        self.team_model = QStringListModel([str(team["name"]) for team in self.teams])
        self.team_list = QListView()
        self.team_list.setModel(self.team_model)
        self.team_list.clicked.connect(self.load_selected_team)
        side_layout.addWidget(self.team_list, 1)
        self.new_button = QPushButton("Nova equipe")
        self.new_button.clicked.connect(self.new_team)
        apply_glow(self.new_button, blur=18)
        side_layout.addWidget(self.new_button)
        root.addWidget(sidebar, 1)

        editor = Card()
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(20, 18, 20, 20)
        editor_layout.addWidget(TitleLabel("Editor de equipe"))
        editor_layout.addWidget(QLabel("Nome da equipe"))
        self.name_entry = QLineEdit("Fusion quickswap")
        editor_layout.addWidget(self.name_entry)
        editor_layout.addWidget(QLabel("Status"))
        self.status_box = QComboBox()
        self.status_box.addItems(["Not started", "Wanted", "In progress", "Finished"])
        editor_layout.addWidget(self.status_box)
        editor_layout.addWidget(QLabel("Personagens"))
        self.characters_entry = QLineEdit("Augusta, Brant, Shorekeeper")
        self.characters_entry.setPlaceholderText("Separe os personagens por vírgula")
        editor_layout.addWidget(self.characters_entry)
        editor_layout.addStretch(1)
        self.save_button = QPushButton("Salvar equipe")
        self.save_button.clicked.connect(self.save_team)
        apply_glow(self.save_button, blur=18)
        editor_layout.addWidget(self.save_button)
        self.status_label = QLabel("Alterações locais prontas para conexão ao storage.")
        self.status_label.setObjectName("muted")
        editor_layout.addWidget(self.status_label)
        root.addWidget(editor, 2)

    def load_selected_team(self) -> None:
        index = self.team_list.currentIndex().row()
        if index >= 0:
            self.selected_team_index = index
            team = self.teams[index]
            self.name_entry.setText(str(team.get("name", "")))
            self.status_box.setCurrentText(str(team.get("status", "Not started")))
            characters = team.get("characters", [])
            if isinstance(characters, list):
                self.characters_entry.setText(", ".join(str(character) for character in characters))
            self.status_label.setText("Equipe selecionada.")

    def new_team(self) -> None:
        self.selected_team_index = -1
        self.name_entry.clear()
        self.status_box.setCurrentIndex(0)
        self.characters_entry.clear()
        self.status_label.setText("Nova equipe pronta para preenchimento.")

    def save_team(self) -> None:
        name = self.name_entry.text().strip() or "Equipe sem nome"
        team = {
            "name": name,
            "status": self.status_box.currentText(),
            "characters": [item.strip() for item in self.characters_entry.text().split(",") if item.strip()],
        }
        if 0 <= self.selected_team_index < len(self.teams):
            self.teams[self.selected_team_index] = team
        else:
            self.teams.append(team)
            self.selected_team_index = len(self.teams) - 1
        self.team_model.setStringList([str(item["name"]) for item in self.teams])
        save_teams(self.teams)
        self.status_label.setText(f"Equipe '{name}' atualizada.")