"""
A4Grid — A4 纸 + mm 网格 + add_axes 绝对定位排版类。

用法：
    from mpl_helpers import A4Grid

    layout = A4Grid(2, 2, paper='A4', left=20, right=15, top=15, bottom=20, hspace=7, wspace=7)
    ax_a = layout.add_subplot(0, 0, label='a')
    ax_b = layout.add_subplot(0, 1, label='b')
    ax_c = layout.add_subplot(1, 0, label='c')
    ax_d = layout.add_subplot(1, 1, label='d')

    # ... 画数据 ...

    layout.finalize(left_ax_name='a', right_ax_name='b')  # 如果只有两图并排
    layout.save('figure.png')

已知坑（来自踩踏经验）：
    - auto_gap 内部调 fig.canvas.draw() 会重置 tick._direction
    - finalize() 在 auto_gap 之后补 tick 设置，所以放最后调
"""

import matplotlib.pyplot as plt


class A4Grid:
    """A4纸+网格布局+add_axes绝对定位。

    支持多种纸张尺寸预设，mosaic 创建，colorbar 嵌入。

    Parameters
    ----------
    rows, cols : int
        网格行数和列数。
    paper : str or tuple
        'A4' (210×297), 'A4_landscape', 'A3', 'single_column' (85×70),
        'double_column' (175×130), 'wide' (180×110),
        或 (w_mm, h_mm) 自定义。
    left, right, top, bottom : float
        页边距，mm。
    hspace, wspace : float
        格子间距，mm。
    dpi : int
        输出 dpi。
    font_scale : float
        字号缩放因子。
    """

    PRESETS = {
        'A4': (210, 297),
        'A4_landscape': (297, 210),
        'A3': (297, 420),
        'single_column': (85, 70),
        'double_column': (175, 130),
        'wide': (180, 110),
    }

    def __init__(self, rows, cols, paper='A4',
                 left=20, right=15, top=15, bottom=20,
                 hspace=5, wspace=5, dpi=300, font_scale=1.0):
        if isinstance(paper, str):
            self.paper_w, self.paper_h = self.PRESETS[paper]
        else:
            self.paper_w, self.paper_h = paper
        self.rows, self.cols = rows, cols
        self.margins = {'left': left, 'right': right, 'top': top, 'bottom': bottom}
        self.hspace, self.wspace = hspace, wspace
        self.font_scale = font_scale
        usable_w = self.paper_w - left - right
        usable_h = self.paper_h - top - bottom
        self.cell_w = (usable_w - (cols - 1) * wspace) / cols
        self.cell_h = (usable_h - (rows - 1) * hspace) / rows
        self.fig = plt.figure(
            figsize=(self.paper_w / 25.4, self.paper_h / 25.4),
            dpi=dpi, facecolor='white',
        )
        self._axes = {}
        self.paper = paper

    def _mm_to_fig(self, x_mm, y_mm, w_mm, h_mm):
        return [
            x_mm / self.paper_w,
            y_mm / self.paper_h,
            w_mm / self.paper_w,
            h_mm / self.paper_h,
        ]

    def _cell_rect(self, row, col, rowspan=1, colspan=1):
        x = self.margins['left'] + col * (self.cell_w + self.wspace)
        y = self.margins['bottom'] + row * (self.cell_h + self.hspace)
        w = self.cell_w + (colspan - 1) * (self.cell_w + self.wspace)
        h = self.cell_h + (rowspan - 1) * (self.cell_h + self.hspace)
        return [x, y, w, h]

    def add_subplot(self, row, col, rowspan=1, colspan=1, label=None):
        """在 (row, col) 位置添加一个子图。label 用于 finalize() 传参。"""
        rect_mm = self._cell_rect(row, col, rowspan, colspan)
        rect = self._mm_to_fig(*rect_mm)
        ax = self.fig.add_axes(rect)
        name = label or f'{row}_{col}'
        self._axes[name] = ax
        return ax

    def get_ax(self, name):
        """通过 label 获取子图。"""
        return self._axes[name]

    @property
    def axes(self):
        """所有子图列表。"""
        return list(self._axes.values())

    def add_colorbar(self, mappable, label='', which='right',
                     size_mm=4, pad_mm=2, fontsize=None):
        """添加 colorbar。"""
        if fontsize is None:
            fontsize = min(12, max(6, round(self.paper_h / 25.4 * 0.4 * self.font_scale)))
        ax = list(self._axes.values())[-1]
        pos = ax.get_position()
        if which == 'right':
            cax = self.fig.add_axes([
                pos.x1 + pad_mm / self.paper_w, pos.y0,
                size_mm / self.paper_w, pos.height,
            ])
        else:
            cax = self.fig.add_axes([
                pos.x0, pos.y0 - pad_mm / self.paper_h - size_mm / self.paper_h,
                pos.width, size_mm / self.paper_h,
            ])
        cb = self.fig.colorbar(mappable, cax=cax)
        cb.set_label(label, fontsize=fontsize)
        cb.ax.tick_params(labelsize=fontsize - 1)
        return cb

    def auto_gap(self, left_name, right_name, extra_padding_mm=3):
        """renderer 实测右图文字向左延伸宽度，自动重排 gap。

        ⚠️ 内部调 fig.canvas.draw() 会重置 tick._direction。
        tick 方向覆盖必须在 auto_gap 之后。推荐用 finalize() 统一处理。
        """
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        inv = self.fig.transFigure.inverted()
        left_ax, right_ax = self._axes[left_name], self._axes[right_name]

        bbox = inv.transform(right_ax.yaxis.label.get_window_extent(renderer))
        extend_mm = (right_ax.get_position().x0 - min(bbox[:, 0])) * self.paper_w

        ext_panel = 0
        for t in left_ax.texts + right_ax.texts:
            b = inv.transform(t.get_window_extent(renderer))
            tb_left = min(b[:, 0])
            for ax in [left_ax, right_ax]:
                e = (ax.get_position().x0 - tb_left) * self.paper_w
                if e > ext_panel:
                    ext_panel = e

        gap = max(extend_mm + ext_panel + extra_padding_mm, 5)
        if gap > self.wspace:
            self.wspace = gap
            usable_w = self.paper_w - self.margins['left'] - self.margins['right']
            self.cell_w = (usable_w - (self.cols - 1) * self.wspace) / self.cols
            for name, ax in self._axes.items():
                idx = list(self._axes.keys()).index(name)
                rect_mm = self._cell_rect(idx // self.cols, idx % self.cols)
                ax.set_position(self._mm_to_fig(*rect_mm))
        return gap

    def finalize(self, left_ax_name=None, right_ax_name=None):
        """一步完成：auto_gap 调整左右间距。

        这是出图前调的最后一行。
        刻度相关全部由 IgneousWR 控制，figkit 不碰。

        Parameters
        ----------
        left_ax_name, right_ax_name : str, optional
            传给 auto_gap() 的标签名。只有两图并排时才需要。
        """
        # 1. auto_gap（可选）
        if left_ax_name and right_ax_name:
            self.auto_gap(left_ax_name, right_ax_name)


    def save(self, path=None, bbox_inches=None, pad_inches=0.05,
             transparent=False, dpi=None):
        """保存图片。不传 bbox_inches 时保留精确 mm 定位。"""
        if path is None:
            path = f'Figure_{self.paper if isinstance(self.paper, str) else "custom"}.png'
        ext = path.rsplit('.', 1)[-1].lower()
        fmt = ext if ext in ('pdf', 'svg', 'eps') else None
        self.fig.savefig(
            path, dpi=dpi or self.fig.dpi, format=fmt,
            bbox_inches=bbox_inches, pad_inches=pad_inches,
            transparent=transparent,
        )
        plt.close(self.fig)
