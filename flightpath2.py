import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

class EnhancedFlightProfileEditor:
    def __init__(self):
        # Initial coordinates: [time_mins, altitude_k_ft]
        self.points = [
            [1.0, 0.0], [7.0, 0.0], [12.0, 0.0], [15.0, 0.0],
            [23.0, 40.0], [39.0, 40.0], [41.0, 26.0], [45.0, 0.0],
            [54.0, 0.0], [55.0, 5.0], [65.0, 36.0], [82.0, 36.0],
            [83.0, 33.0], [91.0, 0.0], [99.0, 5.0], [104.0, 5.0],
            [106.0, 1.5], [116.0, 0.0]
        ]

        # Labels attached by point index initially
        initial_labels = {
            0: "ENGINES RUNNING", 1: "180° TURN F/O & CAPT",
            2: "DELAYED WINGTIPS EXTENSION", 3: "HUD TAKEOFF",
            4: "VSD DEMO", 6: "ILS", 8: "HUD TAKEOFF",
            9: "ENG FAIL R (SEVERE DAMAGE)", 12: "RNAV Y (LPV MINIMA)",
            13: "OEI G/A & M/A", 14: "[ ] FUEL IMBALANCE",
            15: "[ ] WINGTIPS DRIVE FAULT", 16: "OEI MANUAL ILS",
            17: "AFTER LANDING"
        }
        self.labels = [initial_labels.get(i, "") for i in range(len(self.points))]

        # Setup Figure & Styling
        self.fig, self.ax = plt.subplots(figsize=(14, 8))
        self.fig.canvas.manager.set_window_title("Interactive Flight Profile Editor")
        self.ax.set_facecolor("#d7ecf8")
        self.ax.set_xlim(-2, 126)
        self.ax.set_ylim(-2, 72)
        self.ax.set_xlabel("TIME (Mins)", fontsize=11, fontweight="bold", labelpad=8)
        self.ax.set_ylabel("ALTITUDE (x1,000)", fontsize=11, fontweight="bold", labelpad=8)

        # Draw shaded vertical flight operational bands
        self._draw_background_bands()

        # Altitude highlight labels (FL 360)
        self.ax.text(23, 34, "FL 360", color="red", fontweight="bold", fontsize=10)
        self.ax.text(65, 34, "FL 360", color="red", fontweight="bold", fontsize=10)

        # Base plot lines and points
        pts_np = np.array(self.points)
        self.line, = self.ax.plot(pts_np[:, 0], pts_np[:, 1], color="#17557d", lw=2.5, zorder=3)
        self.scatter = self.ax.scatter(pts_np[:, 0], pts_np[:, 1], color="#17557d", s=55, zorder=4)

        # Text labels list
        self.text_artists = []
        self._init_labels()

        # Live readout tooltip
        self.tooltip = self.ax.annotate(
            "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="#202020", ec="none", alpha=0.85),
            color="white", fontsize=9, fontweight="bold", zorder=10
        )
        self.tooltip.set_visible(False)

        # Interaction tracking variables
        self.selected_point_idx = None
        self.selected_segment_idx = None
        self.drag_start = None

        # Connect canvas events
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)

    def _draw_background_bands(self):
        """Draws soft gradient vertical zones matching reference flight charts."""
        bands = [(12, 26), (81, 93)]
        for left, right in bands:
            self.ax.axvspan(left, right, color="#b9e0f7", alpha=0.65, zorder=1)

    def _init_labels(self):
        for ann in self.text_artists:
            ann.remove()
        self.text_artists = []
        for i, text in enumerate(self.labels):
            ann = self.ax.annotate(
                text, (self.points[i][0], self.points[i][1]),
                xytext=(0, 10), textcoords="offset points",
                rotation=90, color="#005596", fontsize=8.5,
                fontweight="semibold", ha="center", va="bottom", zorder=5
            )
            self.text_artists.append(ann)

    def _distance_to_segment(self, p, a, b):
        ab = b - a
        norm_ab = np.linalg.norm(ab)
        if norm_ab == 0:
            return np.linalg.norm(p - a), 0.0
        t = np.clip(np.dot(p - a, ab) / (norm_ab ** 2), 0.0, 1.0)
        proj = a + t * ab
        return np.linalg.norm(p - proj), t

    def on_press(self, event):
        if event.inaxes != self.ax:
            return

        click_xy = np.array([event.x, event.y])
        pts_screen = self.ax.transData.transform(np.array(self.points))
        dists = np.linalg.norm(pts_screen - click_xy, axis=1)
        min_idx = np.argmin(dists)

        # --- RIGHT-CLICK: Delete Waypoint ---
        if event.button == 3:
            if dists[min_idx] < 12.0 and len(self.points) > 2:
                del self.points[min_idx]
                del self.labels[min_idx]
                self._init_labels()
                self.update_canvas()
            return

        # --- DOUBLE-CLICK LEFT: Add New Waypoint ---
        if event.button == 1 and event.dblclick:
            for i in range(len(self.points) - 1):
                dist, t = self._distance_to_segment(click_xy, pts_screen[i], pts_screen[i + 1])
                if dist < 10.0:
                    new_point = [float(event.xdata), max(0.0, float(event.ydata))]
                    self.points.insert(i + 1, new_point)
                    self.labels.insert(i + 1, "")
                    self._init_labels()
                    self.update_canvas()
                    return

        # --- SINGLE-CLICK LEFT: Select for Dragging ---
        if event.button == 1 and not event.dblclick:
            if dists[min_idx] < 12.0:
                self.selected_point_idx = min_idx
                self._show_tooltip(self.points[min_idx][0], self.points[min_idx][1])
                return

            for i in range(len(self.points) - 1):
                dist, _ = self._distance_to_segment(click_xy, pts_screen[i], pts_screen[i + 1])
                if dist < 8.0:
                    self.selected_segment_idx = i
                    self.drag_start = (event.xdata, event.ydata)
                    return

    def on_motion(self, event):
        if event.inaxes != self.ax:
            return

        # 1. Moving a single checkpoint
        if self.selected_point_idx is not None:
            idx = self.selected_point_idx
            new_x = float(event.xdata)
            new_y = max(0.0, float(event.ydata))  # Altitude cannot drop below 0

            # Time ordering constraint (cannot cross left or right neighbor)
            min_x = self.points[idx - 1][0] if idx > 0 else -2.0
            max_x = self.points[idx + 1][0] if idx < len(self.points) - 1 else 125.0
            new_x = np.clip(new_x, min_x + 0.05, max_x - 0.05)

            self.points[idx] = [new_x, new_y]
            self._show_tooltip(new_x, new_y)
            self.update_canvas()

        # 2. Moving an entire segment
        elif self.selected_segment_idx is not None:
            dx = event.xdata - self.drag_start[0]
            dy = event.ydata - self.drag_start[1]
            idx = self.selected_segment_idx

            p1, p2 = self.points[idx], self.points[idx + 1]
            # Verify non-negative altitude constraint
            if p1[1] + dy >= 0 and p2[1] + dy >= 0:
                # Verify neighbor order constraint
                min_x = self.points[idx - 1][0] if idx > 0 else -2.0
                max_x = self.points[idx + 2][0] if idx + 2 < len(self.points) else 125.0

                if (p1[0] + dx > min_x) and (p2[0] + dx < max_x):
                    self.points[idx] = [p1[0] + dx, p1[1] + dy]
                    self.points[idx + 1] = [p2[0] + dx, p2[1] + dy]
                    self.drag_start = (event.xdata, event.ydata)
                    self.update_canvas()

    def on_release(self, event):
        self.selected_point_idx = None
        self.selected_segment_idx = None
        self.drag_start = None
        self.tooltip.set_visible(False)
        self.fig.canvas.draw_idle()

    def _show_tooltip(self, x, y):
        self.tooltip.xy = (x, y)
        self.tooltip.set_text(f"T: {x:.1f}m\nAlt: {y:.1f}k")
        self.tooltip.set_visible(True)

    def on_key_press(self, event):
        if event.key in ['s', 'S']:
            export_data = [
                {"time_min": round(p[0], 2), "altitude_kft": round(p[1], 2), "label": lbl}
                for p, lbl in zip(self.points, self.labels)
            ]
            with open("flight_profile.json", "w") as f:
                json.dump(export_data, f, indent=4)
            print("Successfully saved updated points to 'flight_profile.json'!")

    def update_canvas(self):
        pts = np.array(self.points)
        self.line.set_data(pts[:, 0], pts[:, 1])
        self.scatter.set_offsets(pts)
        for i, ann in enumerate(self.text_artists):
            ann.xy = (self.points[i][0], self.points[i][1])
        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    editor = EnhancedFlightProfileEditor()
    plt.show()
