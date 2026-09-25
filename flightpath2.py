%matplotlib qt
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.widgets import TextBox

# Closes all previously opened figures to ensure only ONE window appears
plt.close('all')

class FullFlightProfileEditor:
    def __init__(self):
        # 1. Initial coordinates: [time_mins, altitude_k_ft]
        self.points = [
            [1.0, 0.0], [7.0, 0.0], [12.0, 0.0], [15.0, 0.0],
            [23.0, 40.0], [39.0, 40.0], [41.0, 26.0], [45.0, 0.0],
            [54.0, 0.0], [55.0, 5.0], [65.0, 36.0], [82.0, 36.0],
            [83.0, 33.0], [91.0, 0.0], [99.0, 5.0], [104.0, 5.0],
            [106.0, 1.5], [116.0, 0.0]
        ]

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

        # 2. Figure Setup
        self.fig, self.ax = plt.subplots(figsize=(14, 8))
        self.fig.canvas.manager.set_window_title("Flight Profile Editor")
        plt.subplots_adjust(bottom=0.14)
        self.ax.set_facecolor("#d7ecf8")
        self.ax.set_xlim(-2, 126)
        self.ax.set_ylim(-2, 72)
        self.ax.set_xlabel("TIME (Mins)", fontsize=11, fontweight="bold", labelpad=8)
        self.ax.set_ylabel("ALTITUDE (x1,000)", fontsize=11, fontweight="bold", labelpad=8)

        # 3. Draggable Bands (Constructed as Rectangles for clean updating)
        self.bands_data = [
            {"left": 12.0, "right": 26.0},
            {"left": 81.0, "right": 93.0}
        ]
        self.band_patches = []
        for b in self.bands_data:
            rect = Rectangle(
                (b["left"], -5), b["right"] - b["left"], 80,
                color="#b9e0f7", alpha=0.65, zorder=1
            )
            self.ax.add_patch(rect)
            self.band_patches.append(rect)

        # 4. Draggable FL Labels
        self.fl_labels_data = [
            {"text": "FL 360", "pos": [23.0, 34.0]},
            {"text": "FL 360", "pos": [65.0, 34.0]}
        ]
        self.fl_artists = [
            self.ax.text(fl["pos"][0], fl["pos"][1], fl["text"],
                         color="red", fontweight="bold", fontsize=10, zorder=6)
            for fl in self.fl_labels_data
        ]

        # 5. Profile Line & Scatter Points
        pts_np = np.array(self.points)
        self.line, = self.ax.plot(pts_np[:, 0], pts_np[:, 1], color="#17557d", lw=2.5, zorder=3)
        self.scatter = self.ax.scatter(pts_np[:, 0], pts_np[:, 1], color="#17557d", s=55, zorder=4)

        # Labels
        self.text_artists = []
        self._init_labels()

        # Tooltip HUD
        self.tooltip = self.ax.annotate(
            "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="#202020", ec="none", alpha=0.85),
            color="white", fontsize=9, fontweight="bold", zorder=10
        )
        self.tooltip.set_visible(False)

        # 6. Integrated Label Input Box
        box_ax = plt.axes([0.30, 0.025, 0.45, 0.045])
        self.textbox = TextBox(box_ax, 'Edit Selected Label: ', initial='')
        self.textbox.on_submit(self.on_text_submit)

        # Interaction State Variables
        self.active_editing = None
        self.selected_point_idx = None
        self.selected_segment_idx = None
        self.selected_fl_idx = None
        self.selected_band_idx = None
        self.band_drag_mode = None  # 'move', 'left_edge', 'right_edge'
        self.drag_start = None

        # Events
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)

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
            return np.linalg.norm(p - a)
        t = np.clip(np.dot(p - a, ab) / (norm_ab ** 2), 0.0, 1.0)
        proj = a + t * ab
        return np.linalg.norm(p - proj)

    def on_text_submit(self, new_text):
        if not self.active_editing:
            return
        target, idx = self.active_editing
        if target == 'point' and idx < len(self.labels):
            self.labels[idx] = new_text
            self.text_artists[idx].set_text(new_text)
        elif target == 'fl' and idx < len(self.fl_labels_data):
            self.fl_labels_data[idx]["text"] = new_text
            self.fl_artists[idx].set_text(new_text)
        self.fig.canvas.draw_idle()

    def on_press(self, event):
        if event.inaxes != self.ax:
            return

        click_xy = np.array([event.x, event.y])
        pts_screen = self.ax.transData.transform(np.array(self.points))
        dists = np.linalg.norm(pts_screen - click_xy, axis=1)
        min_idx = np.argmin(dists)

        # 1. DELETE POINT (Right-Click)
        if event.button == 3:
            if dists[min_idx] < 12.0 and len(self.points) > 2:
                del self.points[min_idx]
                del self.labels[min_idx]
                self.active_editing = None
                self.textbox.set_val("")
                self._init_labels()
                self.update_canvas()
            return

        # 2. ADD POINT (Double-Click on a line)
        if event.button == 1 and event.dblclick:
            for i in range(len(self.points) - 1):
                if self._distance_to_segment(click_xy, pts_screen[i], pts_screen[i + 1]) < 10.0:
                    new_pt = [float(event.xdata), max(0.0, float(event.ydata))]
                    insert_idx = i + 1
                    self.points.insert(insert_idx, new_pt)
                    self.labels.insert(insert_idx, "WAYPOINT")
                    self._init_labels()
                    self.update_canvas()
                    self.active_editing = ('point', insert_idx)
                    self.textbox.set_val(self.labels[insert_idx])
                    return

        if event.button != 1:
            return

        # 3. CLICKING FL LABELS
        for idx, fl_artist in enumerate(self.fl_artists):
            if fl_artist.get_window_extent(self.fig.canvas.get_renderer()).contains(event.x, event.y):
                self.active_editing = ('fl', idx)
                self.textbox.set_val(self.fl_labels_data[idx]["text"])
                self.selected_fl_idx = idx
                self.drag_start = (event.xdata, event.ydata)
                return

        # 4. CLICKING WAYPOINT DOTS
        if dists[min_idx] < 12.0:
            self.active_editing = ('point', min_idx)
            self.textbox.set_val(self.labels[min_idx])
            self.selected_point_idx = min_idx
            self._show_tooltip(self.points[min_idx][0], self.points[min_idx][1])
            return

        # 5. CLICKING LINE SEGMENTS
        for i in range(len(self.points) - 1):
            if self._distance_to_segment(click_xy, pts_screen[i], pts_screen[i + 1]) < 8.0:
                self.selected_segment_idx = i
                self.drag_start = (event.xdata, event.ydata)
                return

        # 6. CLICKING / RESIZING BANDS
        edge_thresh = 2.0  # Time units threshold for border resizing
        for idx, band in enumerate(self.bands_data):
            if abs(event.xdata - band["left"]) <= edge_thresh:
                self.selected_band_idx = idx
                self.band_drag_mode = 'left_edge'
                self.drag_start = (event.xdata, event.ydata)
                self._show_band_tooltip(event.xdata, event.ydata, f"Band {idx+1}: Left Edge")
                return
            elif abs(event.xdata - band["right"]) <= edge_thresh:
                self.selected_band_idx = idx
                self.band_drag_mode = 'right_edge'
                self.drag_start = (event.xdata, event.ydata)
                self._show_band_tooltip(event.xdata, event.ydata, f"Band {idx+1}: Right Edge")
                return
            elif band["left"] <= event.xdata <= band["right"]:
                self.selected_band_idx = idx
                self.band_drag_mode = 'move'
                self.drag_start = (event.xdata, event.ydata)
                self._show_band_tooltip(event.xdata, event.ydata, f"Band {idx+1}: Moving")
                return

    def on_motion(self, event):
        if event.inaxes != self.ax:
            return

        # Move FL label
        if self.selected_fl_idx is not None:
            dx = event.xdata - self.drag_start[0]
            dy = event.ydata - self.drag_start[1]
            pos = self.fl_labels_data[self.selected_fl_idx]["pos"]
            pos[0] += dx
            pos[1] += dy
            self.fl_artists[self.selected_fl_idx].set_position((pos[0], pos[1]))
            self.drag_start = (event.xdata, event.ydata)
            self.fig.canvas.draw_idle()
            return

        # Move or Resize Bands
        if self.selected_band_idx is not None:
            dx = event.xdata - self.drag_start[0]
            band = self.bands_data[self.selected_band_idx]
            
            if self.band_drag_mode == 'move':
                band["left"] += dx
                band["right"] += dx
                self._show_band_tooltip(event.xdata, event.ydata, f"Band: [{band['left']:.1f} - {band['right']:.1f}]")
            elif self.band_drag_mode == 'left_edge':
                if band["left"] + dx < band["right"] - 1.0:
                    band["left"] += dx
                self._show_band_tooltip(band["left"], event.ydata, f"Left: {band['left']:.1f}m")
            elif self.band_drag_mode == 'right_edge':
                if band["right"] + dx > band["left"] + 1.0:
                    band["right"] += dx
                self._show_band_tooltip(band["right"], event.ydata, f"Right: {band['right']:.1f}m")

            self.drag_start = (event.xdata, event.ydata)
            self._update_bands()
            return

        # Move single dot
        if self.selected_point_idx is not None:
            idx = self.selected_point_idx
            new_x = float(event.xdata)
            new_y = max(0.0, float(event.ydata))

            min_x = self.points[idx - 1][0] if idx > 0 else -2.0
            max_x = self.points[idx + 1][0] if idx < len(self.points) - 1 else 125.0
            new_x = np.clip(new_x, min_x + 0.05, max_x - 0.05)

            self.points[idx] = [new_x, new_y]
            self._show_tooltip(new_x, new_y)
            self.update_canvas()

        # Move line segment
        elif self.selected_segment_idx is not None:
            dx = event.xdata - self.drag_start[0]
            dy = event.ydata - self.drag_start[1]
            idx = self.selected_segment_idx

            p1, p2 = self.points[idx], self.points[idx + 1]
            if p1[1] + dy >= 0 and p2[1] + dy >= 0:
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
        self.selected_fl_idx = None
        self.selected_band_idx = None
        self.band_drag_mode = None
        self.drag_start = None
        self.tooltip.set_visible(False)
        self.fig.canvas.draw_idle()

    def _show_tooltip(self, x, y):
        self.tooltip.xy = (x, y)
        self.tooltip.set_text(f"T: {x:.1f}m\nAlt: {y:.1f}k")
        self.tooltip.set_visible(True)

    def _show_band_tooltip(self, x, y, msg):
        self.tooltip.xy = (x, y)
        self.tooltip.set_text(msg)
        self.tooltip.set_visible(True)

    def _update_bands(self):
        for idx, rect in enumerate(self.band_patches):
            b = self.bands_data[idx]
            rect.set_x(b["left"])
            rect.set_width(b["right"] - b["left"])
        self.fig.canvas.draw_idle()

    def on_key_press(self, event):
        if event.key in ['s', 'S']:
            export_data = {
                "points": [
                    {"time_min": round(p[0], 2), "altitude_kft": round(p[1], 2), "label": lbl}
                    for p, lbl in zip(self.points, self.labels)
                ],
                "bands": [
                    {"left": round(b["left"], 2), "right": round(b["right"], 2)}
                    for b in self.bands_data
                ],
                "fl_labels": [
                    {"text": fl["text"], "time_min": round(fl["pos"][0], 2), "altitude_kft": round(fl["pos"][1], 2)}
                    for fl in self.fl_labels_data
                ]
            }
            with open("flight_profile.json", "w") as f:
                json.dump(export_data, f, indent=4)
            print("Exported flight profile data to 'flight_profile.json'!")

    def update_canvas(self):
        pts = np.array(self.points)
        self.line.set_data(pts[:, 0], pts[:, 1])
        self.scatter.set_offsets(pts)
        for i, ann in enumerate(self.text_artists):
            ann.xy = (self.points[i][0], self.points[i][1])
        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    editor = FullFlightProfileEditor()
    plt.show()
