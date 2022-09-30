import urwid as u
from pop_up import ThingWithAPopUp
import subprocess
import requests
import base64
from requests.auth import HTTPBasicAuth
import os
import urllib.parse

show_branches_CMD = ["git", "branch"]
checkout_branch_CMD = ["git", "checkout"]

jira_root_url = os.environ.get("JIRA_URL", "")
api = "rest/api/2/search"
jira_user = os.environ.get("JIRA_USER", "")
jira_token = os.environ.get("JIRA_TOKEN", "")


def get_jira_info() -> str:
    """
    Get Jira issue from branch name
    """

    headers = {"Accept": "application/json"}
    auth = HTTPBasicAuth(jira_user, jira_token)

    query = {
        "jql": """status in (Approved, "Code Review", "CODE REVIEW", Draft, "In Progress", "IN PROGRESS", "In Review", "IN REVIEW", Open, OPEN, Published, QA, "To Do") AND assignee in (currentUser()) ORDER BY created DESC"""
    }

    response = requests.request(
        "GET",
        urllib.parse.urljoin(jira_root_url, api),
        headers=headers,
        params=query,
        auth=auth,
    )
    if response.status_code == 200:
        issues = response.json()["issues"]
        issue_map = {
            issue["key"]: {
                "title": issue["fields"]["summary"],
                "description": issue["fields"]["description"],
            }
            for issue in issues
        }
        return issue_map
    return {}


class ListItem(u.WidgetWrap):
    def __init__(self, branch):

        self.content = branch

        name = branch["name"]

        t = u.AttrWrap(u.Text(name), "branch", "branch_selected")
        # ThingWithAPopUp(t)
        u.WidgetWrap.__init__(self, t)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


class ListView(u.WidgetWrap):
    def __init__(self):

        u.register_signal(self.__class__, ["show_details"])

        self.walker = u.SimpleFocusListWalker([])

        lb = u.ListBox(self.walker)

        u.WidgetWrap.__init__(self, lb)

    def modified(self):

        focus_w, _ = self.walker.get_focus()

        u.emit_signal(self, "show_details", focus_w.content)

    def set_data(self, branches):

        branches_widgets = [ListItem(c) for c in branches]
        position = 0
        for index, content in enumerate(branches):
            if "*" in content["name"]:
                position = index
                break

        u.disconnect_signal(self.walker, "modified", self.modified)

        while len(self.walker) > 0:
            self.walker.pop()

        self.walker.extend(branches_widgets)

        u.connect_signal(self.walker, "modified", self.modified)

        self.walker.set_focus(position)


class DetailView(u.WidgetWrap):
    def __init__(self):
        t = u.Text("")
        u.WidgetWrap.__init__(self, t)

    def set_branch(self, c):
        detail = c["detail"]
        content = detail["description"].replace("\n", "\n" + " " * 10)
        s = f"Title   : {detail['title']}\nContent : {content}"
        self._w.set_text(s)


class OverlayView(u.WidgetWrap):
    def __init__(self):
        t = u.Text("")
        u.WidgetWrap.__init__(self, t)

    def set_alert(self, c):
        text = c
        self._w.set_text(text)


class App(object):
    def unhandled_input(self, key):
        walker = self.list_view.walker
        if key in ("enter",):
            focus, position = walker.get_focus()
            try:
                self.checkout_banch(focus.content)
            except Exception as e:
                self.overlay_view.set_alert(str(e))
                self.toggle_overlay()
            self.update_data()
            walker.set_focus(position)

        if key in ("q",):
            raise u.ExitMainLoop()
        if key in ("j",):
            _, position = walker.get_focus()
            try:
                walker.set_focus(walker.next_position(position))
            except IndexError:
                pass
        if key in ("k",):
            _, position = walker.get_focus()
            try:
                walker.set_focus(walker.prev_position(position))
            except IndexError:
                pass

    def show_details(self, branch):
        self.detail_view.set_branch(branch)

    def __init__(self):

        self.palette = {
            ("bg", "black", "dark gray"),
            ("branch", "black", "dark gray"),
            ("branch_selected", "black", "yellow"),
            ("footer", "white, bold", "dark red"),
        }

        self.list_view = ListView()
        self.detail_view = DetailView()
        self.overlay_view = OverlayView()

        u.connect_signal(self.list_view, "show_details", self.show_details)

        footer = u.AttrWrap(u.Text(" Q to exit"), "footer")

        col_rows = u.raw_display.Screen().get_cols_rows()
        h = col_rows[0] - 2

        f1 = u.Filler(self.list_view, valign="top", height=h)
        f2 = u.Filler(self.detail_view, valign="top")
        f3 = u.Filler(self.overlay_view)

        c_list = u.LineBox(f1, title="Branches")
        c_details = u.LineBox(f2, title="Branch Details")
        c_overlay = u.LineBox(f3, title="Error")

        columns = u.Columns(
            [
                ("weight", 30, c_list),
                ("weight", 70, c_details),
            ]
        )

        self.frame = u.AttrMap(u.Frame(body=columns, footer=footer), "bg")
        self.overlay = u.Overlay(c_overlay, self.frame, "center", 50, "middle", 10)

        self.loop = u.MainLoop(
            self.frame, self.palette, unhandled_input=self.unhandled_input, pop_ups=True
        )

    def toggle_overlay(self):
        if self.loop.widget == self.frame:
            self.loop.widget = self.overlay
        else:
            self.loop.widget = self.frame

    def checkout_banch(self, branch):
        result = subprocess.run(
            checkout_branch_CMD + [branch["name"].strip("*").strip(" ")],
            capture_output=True,
        )
        if result.returncode != 0:
            raise Exception(result.stderr.decode("utf-8"))

    def update_data(self):
        branches = (
            subprocess.check_output(show_branches_CMD).decode("utf-8").split("\n")
        )
        l = {branch: {"title": "", "description": ""} for branch in branches}
        issues = get_jira_info()
        for issue, content in issues.items():
            for branch in branches:
                if issue in branch:
                    l[branch] = content
                    break
        l = [{"name": k, "detail": v} for k, v in l.items()]
        self.list_view.set_data(l)

    def start(self):
        self.update_data()
        self.loop.run()


def main():
    app = App()
    app.start()
