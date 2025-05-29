"""
Czyste style aplikacji - usuwa problematyczne CSS dla Tree
"""

APP_CSS = """
/* Podstawowe layout */
Screen {
    layout: vertical;
}

/* Title bar */
TitleStatusBar {
    layout: horizontal;
    height: 3;
    background: $primary;
}

#title-status {
    layout: horizontal;
    height: 3;
    width: 100%;
}

#title {
    width: 1fr;
    text-style: bold;
    content-align: left middle;
    padding: 0 1;
}

#status {
    width: auto;
    content-align: right middle;
    padding: 0 1;
}

/* Editor section */
#editor-section {
    height: 1fr;
    layout: horizontal;
}

#tree-panel {
    width: 25%;
    border-right: solid $primary;
    padding: 1;
}

#content-panel {
    width: 75%;
    layout: vertical;
    padding: 1;
}

/* Content views */
FileContentView, FolderContentView {
    height: 100%;
    layout: vertical;
}

#file-title, #folder-title {
    height: 3;
    background: $accent;
    padding: 0 1;
    text-style: bold;
    content-align: left middle;
}

#file-content, #folder-content {
    height: 1fr;
    border: solid $primary;
    margin: 1 0;
}

#file-prompt-section, #folder-prompt-section {
    height: auto;
    layout: vertical;
    margin: 1 0;
}

#file-actions, #folder-actions {
    layout: horizontal;
    height: auto;
    margin: 1 0;
}

#file-prompt, #folder-prompt {
    height: 3;
    margin: 0 0 1 0;
}

Button {
    margin: 0 1;
    height: 3;
    min-width: 8;
}

#file-metadata {
    height: 3;
    background: $surface;
    padding: 0 1;
    text-style: italic;
    content-align: left middle;
}

/* Logs */
LogsSection {
    height: 3;
    background: $surface;
    border-top: solid $primary;
}

#logs {
    height: 3;
    padding: 0 1;
    text-style: italic;
    content-align: left middle;
}

/* Main prompt */
MainPromptSection {
    height: 8;
    border-top: solid $primary;
    padding: 1;
}

#main-prompt-section {
    height: 6;
    layout: vertical;
}

#main-prompt-container {
    layout: horizontal;
    height: 3;
    margin: 1 0;
}

#main-prompt {
    width: 1fr;
    height: 3;
    margin-right: 1;
}

#main-buttons {
    layout: horizontal;
    width: auto;
}

#main-send, #main-reset {
    width: 10;
    height: 3;
    margin: 0 1;
}

#main-prompt-title {
    height: 1;
    text-style: bold;
    margin: 0 0 1 0;
}
"""