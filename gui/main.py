#!/usr/bin/env python3
"""
GUI Entry Point
Modular, clean architecture
"""

from gui.app import AgentDashboard


def main():
    """Entry point for GUI application"""
    app = AgentDashboard()
    app.run()


if __name__ == "__main__":
    main()