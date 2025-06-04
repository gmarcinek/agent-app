"""
Minimalny footer z mikroskopijnymi kontrolkami
"""
from textual.widgets import Footer
from textual.binding import Binding

from registry.process_manager import ProcessManager

class ProcessFooter(Footer):
    """Mikroskopijny footer z statusami procesów i kontrolkami"""
    
    BINDINGS = [
        Binding("ctrl+r", "restart", "Reset", show=True),
        Binding("ctrl+q", "stop_all", "Turn Off", show=True),
    ]
    
    def __init__(self, process_manager: ProcessManager):
        super().__init__()
        self.process_manager = process_manager
    
    def on_mount(self):
        """Aktualizacja statusu co sekundę"""
        self.set_interval(1.0, self.update_status_display)
        self.update_status_display()
    
    def update_status_display(self):
        """Aktualizuje wyświetlany status procesów"""
        status = self.process_manager.get_status()
        
        # Mapowanie kolorów dla statusów (jako emotikony)
        color_map = {
            "running": "🟢",
            "starting": "🟡", 
            "error": "🔴",
            "stopped": "⚫"
        }
        
        # Generuj kompaktowy status
        status_parts = []
        for name, state in status.items():
            icon = color_map.get(state, "⚫")
            # Skróć nazwy: agent->A, analyser->An, synthetiser->S
            short_name = {"agent": "A", "analyser": "An", "synthetiser": "S"}.get(name, name[0])
            status_parts.append(f"{icon}{short_name}")
        
        # Ustaw custom text w footer
        self.styles.content = " ".join(status_parts)
    
    def action_restart(self):
        """Restart wszystkich procesów - Ctrl+R"""
        self.process_manager.stop_all()
        self.app.notify("🔄 Restarting all processes...")
        self.app.set_timer(2.0, lambda: self.process_manager.start_all())
    
    def action_stop_all(self):
        """Stop wszystkich procesów - Ctrl+Q"""
        self.process_manager.stop_all()
        self.app.notify("⏹️ All processes stopped")