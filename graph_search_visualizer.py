import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import heapq
from collections import deque
import math


class GraphSearchVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Graph Search Visualizer")
        self.root.geometry("1150x760")
        self.root.minsize(900, 600)
        self.root.configure(bg="#101827")

        # Graph data
        self.nodes = {}
        self.edges = {}
        self.next_id = 1
        self.start = None
        self.goal = None
        self.selected = None

        # Interface state
        self.mode = tk.StringVar(value="add")
        self.algorithm = tk.StringVar(value="A*")
        self.directed = tk.BooleanVar(value=False)

        # Search visualization state
        self.path = []
        self.explored = []
        self.result_text = tk.StringVar(
            value="Build a graph to get started."
        )

        self.build_ui()
        self.draw_graph()

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#101827")
        header.pack(fill="x", padx=20, pady=15)

        tk.Label(
            header,
            text="GRAPH SEARCH VISUALIZER",
            font=("Segoe UI", 20, "bold"),
            fg="#60A5FA",
            bg="#101827"
        ).pack(side="left")

        tk.Label(
            header,
            text="5 Search Algorithms",
            font=("Segoe UI", 10),
            fg="#94A3B8",
            bg="#101827"
        ).pack(side="right")

        # Main layout
        main = tk.Frame(self.root, bg="#101827")
        main.pack(fill="both", expand=True, padx=20, pady=5)

        # Left sidebar
        sidebar = tk.Frame(main, bg="#1E293B", width=245)
        sidebar.pack(side="left", fill="y", padx=(0, 15))
        sidebar.pack_propagate(False)

        self.section(sidebar, "GRAPH TOOLS")

        tools = [
            ("Add Node", "add"),
            ("Connect Nodes", "connect"),
            ("Set Start Node", "start"),
            ("Set Goal Node", "goal"),
            ("Edit Heuristic", "heuristic"),
            ("Delete Node", "delete")
        ]

        self.mode_buttons = {}

        for label, mode in tools:
            button = tk.Button(
                sidebar,
                text=label,
                command=lambda selected_mode=mode: self.set_mode(
                    selected_mode
                ),
                font=("Segoe UI", 10, "bold"),
                bg="#334155",
                fg="white",
                activebackground="#2563EB",
                activeforeground="white",
                relief="flat",
                padx=10,
                pady=9,
                cursor="hand2"
            )
            button.pack(fill="x", padx=12, pady=4)
            self.mode_buttons[mode] = button

        self.section(sidebar, "ALGORITHM")

        self.algorithm_box = ttk.Combobox(
            sidebar,
            textvariable=self.algorithm,
            values=["A*", "BFS", "DFS", "Greedy", "UCS"],
            state="readonly",
            font=("Segoe UI", 11)
        )
        self.algorithm_box.pack(fill="x", padx=12, pady=5)
        self.algorithm_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.clear_visualization()
        )

        tk.Checkbutton(
            sidebar,
            text="Directed Graph",
            variable=self.directed,
            bg="#1E293B",
            fg="white",
            selectcolor="#334155",
            activebackground="#1E293B",
            activeforeground="white",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=12, pady=8)

        self.section(sidebar, "ACTIONS")

        self.action_button(
            sidebar, "▶  Run Search", self.run_search, "#2563EB"
        )
        self.action_button(
            sidebar, "Reset Visualization",
            self.clear_visualization, "#475569"
        )
        self.action_button(
            sidebar, "Clear Graph", self.clear_graph, "#991B1B"
        )

        self.section(sidebar, "LEGEND")

        legend_items = [
            ("#22C55E", "Start Node"),
            ("#EF4444", "Goal Node"),
            ("#F59E0B", "Explored Node"),
            ("#A855F7", "Final Path"),
            ("#64748B", "Normal Node")
        ]

        for color, label in legend_items:
            row = tk.Frame(sidebar, bg="#1E293B")
            row.pack(fill="x", padx=15, pady=3)

            tk.Label(
                row,
                text="●",
                fg=color,
                bg="#1E293B",
                font=("Arial", 14)
            ).pack(side="left")

            tk.Label(
                row,
                text=label,
                fg="#CBD5E1",
                bg="#1E293B",
                font=("Segoe UI", 9)
            ).pack(side="left", padx=8)

        # Right workspace
        workspace = tk.Frame(main, bg="#101827")
        workspace.pack(side="left", fill="both", expand=True)

        # IMPORTANT: Create the instruction label BEFORE set_mode().
        # set_mode() updates this label, so it must already exist.
        self.instruction = tk.Label(
            workspace,
            text="Click anywhere on the canvas to add a node.",
            font=("Segoe UI", 10),
            bg="#1E293B",
            fg="#CBD5E1",
            anchor="w",
            padx=12,
            pady=10
        )
        self.instruction.pack(fill="x", pady=(0, 10))

        # Now it is safe to initialize the selected tool.
        self.set_mode("add")

        # Graph canvas
        self.canvas = tk.Canvas(
            workspace,
            bg="#0B1220",
            highlightthickness=1,
            highlightbackground="#334155"
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.canvas.bind(
            "<Configure>",
            lambda event: self.draw_graph()
        )

        # Results panel
        results = tk.Frame(
            workspace,
            bg="#1E293B",
            padx=15,
            pady=12
        )
        results.pack(fill="x", pady=(12, 0))

        tk.Label(
            results,
            text="SEARCH RESULTS",
            bg="#1E293B",
            fg="#60A5FA",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")

        self.result_label = tk.Label(
            results,
            textvariable=self.result_text,
            bg="#1E293B",
            fg="#E2E8F0",
            font=("Segoe UI", 10),
            justify="left",
            anchor="w",
            wraplength=750
        )
        self.result_label.pack(fill="x", pady=(7, 0))

    def section(self, parent, title):
        tk.Label(
            parent,
            text=title,
            bg="#1E293B",
            fg="#94A3B8",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=13, pady=(15, 6))

    def action_button(self, parent, text, command, color):
        tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            pady=10
        ).pack(fill="x", padx=12, pady=4)

    def set_mode(self, mode):
        self.mode.set(mode)

        instructions = {
            "add": "Click anywhere on the canvas to add a node.",
            "connect": "Click two nodes to connect them.",
            "start": "Click a node to make it the START.",
            "goal": "Click a node to make it the GOAL.",
            "heuristic": "Click a node to edit its heuristic value.",
            "delete": "Click a node to delete it."
        }

        self.instruction.config(text=instructions[mode])

        for key, button in self.mode_buttons.items():
            button.config(
                bg="#2563EB" if key == mode else "#334155"
            )

        self.selected = None
        if hasattr(self, "canvas"):
            self.draw_graph()

    def find_node(self, x, y):
        for node_id, node in self.nodes.items():
            distance = math.hypot(
                x - node["x"],
                y - node["y"]
            )
            if distance <= 23:
                return node_id
        return None

    def canvas_click(self, event):
        x, y = event.x, event.y
        mode = self.mode.get()

        if mode == "add":
            self.add_node(x, y)
            return

        node_id = self.find_node(x, y)
        if node_id is None:
            return

        if mode == "connect":
            self.connect_node(node_id)

        elif mode == "start":
            self.start = node_id
            self.clear_visualization()

        elif mode == "goal":
            self.goal = node_id
            self.clear_visualization()

        elif mode == "heuristic":
            value = simpledialog.askfloat(
                "Heuristic",
                f"Enter heuristic value for Node {node_id}:",
                minvalue=0,
                parent=self.root
            )
            if value is not None:
                self.nodes[node_id]["h"] = value
                self.clear_visualization()

        elif mode == "delete":
            self.delete_node(node_id)

    def add_node(self, x, y):
        node_id = self.next_id
        self.next_id += 1

        self.nodes[node_id] = {
            "x": x,
            "y": y,
            "h": None
        }
        self.edges[node_id] = {}

        self.clear_visualization()

    def connect_node(self, node_id):
        if self.selected is None:
            self.selected = node_id
            self.draw_graph()
            return

        first = self.selected
        second = node_id
        self.selected = None

        if first == second:
            self.draw_graph()
            return

        weight = simpledialog.askfloat(
            "Edge Weight",
            f"Enter weight from Node {first} to Node {second}:",
            initialvalue=1.0,
            minvalue=0.000001,
            parent=self.root
        )

        if weight is not None:
            self.edges[first][second] = weight

            if not self.directed.get():
                self.edges[second][first] = weight

        self.clear_visualization()

    def delete_node(self, node_id):
        del self.nodes[node_id]
        del self.edges[node_id]

        for neighbors in self.edges.values():
            neighbors.pop(node_id, None)

        if self.start == node_id:
            self.start = None

        if self.goal == node_id:
            self.goal = None

        if self.selected == node_id:
            self.selected = None

        self.clear_visualization()

    def heuristic(self, node_id):
        value = self.nodes[node_id]["h"]

        if value is not None:
            return value

        if self.goal is None:
            return 0

        node = self.nodes[node_id]
        goal = self.nodes[self.goal]

        return math.hypot(
            node["x"] - goal["x"],
            node["y"] - goal["y"]
        )

    # ---------------- SEARCH ALGORITHMS ----------------

    def bfs(self):
        queue = deque([self.start])
        visited = {self.start}
        parent = {}
        explored = []

        while queue:
            current = queue.popleft()
            explored.append(current)

            if current == self.goal:
                break

            for neighbor in self.edges[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

        return self.make_result(parent, explored)

    def dfs(self):
        stack = [self.start]
        visited = {self.start}
        parent = {}
        explored = []

        while stack:
            current = stack.pop()
            explored.append(current)

            if current == self.goal:
                break

            # Reverse neighbors so they are visited in insertion order.
            for neighbor in reversed(list(self.edges[current])):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    stack.append(neighbor)

        return self.make_result(parent, explored)

    def greedy(self):
        counter = 0
        queue = [
            (self.heuristic(self.start), counter, self.start)
        ]
        visited = {self.start}
        parent = {}
        explored = []

        while queue:
            _, _, current = heapq.heappop(queue)
            explored.append(current)

            if current == self.goal:
                break

            for neighbor in self.edges[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    counter += 1
                    heapq.heappush(
                        queue,
                        (
                            self.heuristic(neighbor),
                            counter,
                            neighbor
                        )
                    )

        return self.make_result(parent, explored)

    def ucs(self):
        return self.cost_search(use_heuristic=False)

    def astar(self):
        return self.cost_search(use_heuristic=True)

    def cost_search(self, use_heuristic):
        counter = 0
        distances = {self.start: 0}
        parent = {}
        explored = []

        initial_priority = (
            self.heuristic(self.start)
            if use_heuristic else 0
        )

        queue = [
            (initial_priority, counter, 0, self.start)
        ]

        while queue:
            _, _, cost, current = heapq.heappop(queue)

            # Ignore outdated queue entries.
            if cost > distances.get(current, float("inf")):
                continue

            explored.append(current)

            if current == self.goal:
                break

            for neighbor, weight in self.edges[current].items():
                new_cost = cost + weight

                if new_cost < distances.get(
                    neighbor, float("inf")
                ):
                    distances[neighbor] = new_cost
                    parent[neighbor] = current
                    counter += 1

                    priority = new_cost
                    if use_heuristic:
                        priority += self.heuristic(neighbor)

                    heapq.heappush(
                        queue,
                        (
                            priority,
                            counter,
                            new_cost,
                            neighbor
                        )
                    )

        return self.make_result(parent, explored), distances

    # ---------------- RESULT HANDLING ----------------

    def make_result(self, parent, explored):
        if self.goal not in explored:
            return [], explored

        path = []
        current = self.goal

        while current != self.start:
            if current not in parent:
                return [], explored

            path.append(current)
            current = parent[current]

        path.append(self.start)
        path.reverse()

        return path, explored

    def calculate_cost(self, path):
        cost = 0

        for index in range(len(path) - 1):
            cost += self.edges[path[index]][path[index + 1]]

        return cost

    def run_search(self):
        if not self.nodes:
            messagebox.showwarning(
                "Warning",
                "Create some nodes first."
            )
            return

        if self.start not in self.nodes or self.goal not in self.nodes:
            messagebox.showwarning(
                "Missing Nodes",
                "Please select both a start node and a goal node."
            )
            return

        self.clear_visualization()
        algorithm = self.algorithm.get()

        if algorithm == "BFS":
            path, explored = self.bfs()
            cost = self.calculate_cost(path) if path else None

        elif algorithm == "DFS":
            path, explored = self.dfs()
            cost = self.calculate_cost(path) if path else None

        elif algorithm == "Greedy":
            path, explored = self.greedy()
            cost = self.calculate_cost(path) if path else None

        elif algorithm == "UCS":
            (path, explored), distances = self.ucs()
            cost = distances.get(self.goal) if path else None

        elif algorithm == "A*":
            (path, explored), distances = self.astar()
            cost = distances.get(self.goal) if path else None

        else:
            messagebox.showerror(
                "Unknown Algorithm",
                "Please select a valid search algorithm."
            )
            return

        self.path = path
        self.explored = explored

        if path:
            path_text = " → ".join(map(str, path))
            explored_text = " → ".join(map(str, explored))

            self.result_text.set(
                f"Algorithm: {algorithm}\n"
                f"Path: {path_text}\n"
                f"Total Cost: {cost:g}\n"
                f"Explored Nodes: {len(explored)}\n"
                f"Exploration Order: {explored_text}"
            )
        else:
            explored_text = " → ".join(map(str, explored))
            self.result_text.set(
                f"Algorithm: {algorithm}\n"
                f"No path found between Node {self.start} "
                f"and Node {self.goal}.\n"
                f"Explored Nodes: {len(explored)}\n"
                f"Exploration Order: {explored_text or 'None'}"
            )

        self.draw_graph()

    # ---------------- GRAPH DRAWING ----------------

    def draw_graph(self):
        if not hasattr(self, "canvas"):
            return

        self.canvas.delete("all")

        # Draw edges before nodes so nodes appear on top.
        for source, neighbors in self.edges.items():
            for target, weight in neighbors.items():
                if not self.directed.get() and source > target:
                    continue

                if source not in self.nodes or target not in self.nodes:
                    continue

                first = self.nodes[source]
                second = self.nodes[target]

                is_path_edge = False
                if self.path:
                    for index in range(len(self.path) - 1):
                        if (
                            self.path[index] == source
                            and self.path[index + 1] == target
                        ):
                            is_path_edge = True
                            break

                edge_color = (
                    "#A855F7" if is_path_edge else "#64748B"
                )
                edge_width = 4 if is_path_edge else 2

                self.canvas.create_line(
                    first["x"],
                    first["y"],
                    second["x"],
                    second["y"],
                    fill=edge_color,
                    width=edge_width,
                    arrow=(
                        tk.LAST if self.directed.get() else tk.NONE
                    )
                )

                middle_x = (first["x"] + second["x"]) / 2
                middle_y = (first["y"] + second["y"]) / 2

                self.canvas.create_rectangle(
                    middle_x - 18,
                    middle_y - 12,
                    middle_x + 18,
                    middle_y + 12,
                    fill="#0B1220",
                    outline=""
                )

                self.canvas.create_text(
                    middle_x,
                    middle_y,
                    text=str(weight),
                    fill="#CBD5E1",
                    font=("Segoe UI", 9, "bold")
                )

        # Draw nodes.
        for node_id, node in self.nodes.items():
            x = node["x"]
            y = node["y"]

            if node_id == self.start:
                color = "#22C55E"
            elif node_id == self.goal:
                color = "#EF4444"
            elif node_id in self.path:
                color = "#A855F7"
            elif node_id in self.explored:
                color = "#F59E0B"
            elif node_id == self.selected:
                color = "#2563EB"
            else:
                color = "#475569"

            self.canvas.create_oval(
                x - 23,
                y - 23,
                x + 23,
                y + 23,
                fill=color,
                outline="white",
                width=2
            )

            self.canvas.create_text(
                x,
                y,
                text=str(node_id),
                fill="white",
                font=("Segoe UI", 11, "bold")
            )

            if node["h"] is not None:
                self.canvas.create_text(
                    x,
                    y + 36,
                    text=f"h={node['h']:g}",
                    fill="#93C5FD",
                    font=("Segoe UI", 9)
                )

    def clear_visualization(self):
        self.path = []
        self.explored = []
        self.result_text.set(
            "Visualization cleared. Ready to search."
        )
        self.draw_graph()

    def clear_graph(self):
        confirm = messagebox.askyesno(
            "Clear Graph",
            "Are you sure you want to delete the entire graph?"
        )

        if not confirm:
            return

        self.nodes.clear()
        self.edges.clear()
        self.next_id = 1
        self.start = None
        self.goal = None
        self.selected = None

        self.clear_visualization()


if __name__ == "__main__":
    root = tk.Tk()
    app = GraphSearchVisualizer(root)
    root.mainloop()
