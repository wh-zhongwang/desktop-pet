# -*- coding: utf-8 -*-
"""
桌面宠物 - 项目讲解 PPT 生成脚本
使用 python-pptx 生成完整的项目演示文稿
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ============================================================
# 色彩系统（暖色系，契合桌宠可爱风格）
# ============================================================
C_PRIMARY   = RGBColor(0xFF, 0x8C, 0x5A)   # 暖橙
C_SECONDARY = RGBColor(0x5D, 0xAD, 0xE2)   # 天蓝
C_DARK      = RGBColor(0x2C, 0x3E, 0x50)   # 深石板
C_LIGHT     = RGBColor(0xFF, 0xF9, 0xF5)   # 暖白
C_ACCENT    = RGBColor(0xF3, 0x9C, 0x12)   # 琥珀
C_WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
C_GRAY      = RGBColor(0x7F, 0x8C, 0x8D)
C_GREEN     = RGBColor(0x27, 0xAE, 0x60)
C_BG2       = RGBColor(0xFD, 0xF2, 0xE9)   # 浅橙背景

FONT_T = 'Microsoft YaHei'   # 标题字体
FONT_B = 'Microsoft YaHei'   # 正文字体

# 16:9
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H

BLANK = prs.slide_layouts[6]


# ============================================================
# 工具函数
# ============================================================
def add_bg(slide, color):
    """设置幻灯片纯色背景"""
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = color


def add_rect(slide, x, y, w, h, color, line_color=None, line_w=None):
    """添加矩形色块"""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if line_color is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line_color
        if line_w:
            shape.line.width = line_w
    shape.shadow.inherit = False
    return shape


def add_round_rect(slide, x, y, w, h, color, line_color=None, line_w=None):
    """添加圆角矩形"""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if line_color is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line_color
        if line_w:
            shape.line.width = line_w
    shape.shadow.inherit = False
    return shape


def add_oval(slide, x, y, w, h, color, line_color=None, line_w=None):
    """添加椭圆"""
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if line_color is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line_color
        if line_w:
            shape.line.width = line_w
    shape.shadow.inherit = False
    return shape


def add_text(slide, x, y, w, h, text, size=18, color=C_DARK, bold=False,
             align=PP_ALIGN.LEFT, font=FONT_B, anchor=MSO_ANCHOR.TOP,
             line_spacing=None):
    """添加文本框"""
    txBox = slide.shapes.add_textbox(x, y, w, h)
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    if line_spacing:
        tf.paragraphs[0].line_spacing = line_spacing
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font
    p.alignment = align
    # 处理东亚字体
    if p.runs:
        rPr = p.runs[0]._r.get_or_add_rPr()
        ea = rPr.makeelement(qn('a:ea'), {'typeface': font})
        rPr.append(ea)
    return txBox


def add_multi_text(slide, x, y, w, h, lines, size=16, color=C_DARK,
                   align=PP_ALIGN.LEFT, font=FONT_B, line_spacing=1.5,
                   bullet=False):
    """多行文本"""
    txBox = slide.shapes.add_textbox(x, y, w, h)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line if not bullet else '• ' + line
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.font.name = font
        p.alignment = align
        p.line_spacing = line_spacing
        if p.runs:
            rPr = p.runs[0]._r.get_or_add_rPr()
            ea = rPr.makeelement(qn('a:ea'), {'typeface': font})
            rPr.append(ea)
    return txBox


def add_line(slide, x1, y1, x2, y2, color, width=Pt(2)):
    """添加连接线"""
    from pptx.util import Emu
    conn = slide.shapes.add_connector(2, x1, y1, x2, y2)  # straight
    conn.line.color.rgb = color
    conn.line.width = width
    return conn


def page_num(slide, n, total):
    """页码"""
    add_text(slide, Inches(12.3), Inches(7.0), Inches(1), Inches(0.4),
             '%d / %d' % (n, total), size=10, color=C_GRAY,
             align=PP_ALIGN.RIGHT)


def title_bar(slide, title, subtitle=''):
    """统一标题栏"""
    add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(1.15), C_DARK)
    add_rect(slide, Inches(0.6), Inches(0.3), Inches(0.08), Inches(0.55), C_PRIMARY)
    add_text(slide, Inches(0.85), Inches(0.25), Inches(10), Inches(0.65),
             title, size=26, color=C_WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    if subtitle:
        add_text(slide, Inches(0.85), Inches(0.78), Inches(10), Inches(0.3),
                 subtitle, size=12, color=C_GRAY)


TOTAL = 13

# ============================================================
# Slide 1: 封面
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_DARK)
# 装饰圆
add_oval(s, Inches(-1), Inches(-1), Inches(3.5), Inches(3.5), C_PRIMARY)
add_oval(s, Inches(10.8), Inches(4.5), Inches(4), Inches(4), C_SECONDARY)
add_oval(s, Inches(9.5), Inches(-1.5), Inches(2.5), Inches(2.5), C_ACCENT)

# 画一个桌宠角色（用形状拼）
cx, cy = Inches(6.67), Inches(3.6)
add_oval(s, cx + Inches(-0.9), cy + Inches(-1.1), Inches(1.8), Inches(2.2), C_PRIMARY)  # 身体
add_oval(s, cx + Inches(-0.5), cy + Inches(-0.2), Inches(1), Inches(1.5), C_LIGHT)       # 肚皮
add_oval(s, cx + Inches(-0.55), cy + Inches(-0.5), Inches(0.4), Inches(0.4), C_WHITE)   # 左眼
add_oval(s, cx + Inches(0.15), cy + Inches(-0.5), Inches(0.4), Inches(0.4), C_WHITE)    # 右眼
add_oval(s, cx + Inches(-0.42), cy + Inches(-0.4), Inches(0.15), Inches(0.15), C_DARK)  # 左瞳
add_oval(s, cx + Inches(0.28), cy + Inches(-0.4), Inches(0.15), Inches(0.15), C_DARK)   # 右瞳

add_text(s, Inches(1), Inches(5.0), Inches(11.33), Inches(1),
         '桌面宠物  Desktop Pet', size=44, color=C_WHITE, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
add_text(s, Inches(1), Inches(6.0), Inches(11.33), Inches(0.5),
         '物光创新实验室 2026 年招新作品', size=18, color=C_PRIMARY,
         align=PP_ALIGN.CENTER)
add_text(s, Inches(1), Inches(6.5), Inches(11.33), Inches(0.5),
         'Python + tkinter · 零素材 · 自包含可运行', size=14, color=C_GRAY,
         align=PP_ALIGN.CENTER)

# ============================================================
# Slide 2: 目录
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_LIGHT)
title_bar(s, '目录', 'Contents')

items = [
    ('01', '项目背景', '招新任务与设计灵感', C_PRIMARY),
    ('02', '功能总览', '六大核心功能模块', C_SECONDARY),
    ('03', '核心交互', '点击摸头 · 拖拽方向力学', C_ACCENT),
    ('04', '环境感知', '天气换装 · 声音跳舞 · 节日主题', C_GREEN),
    ('05', '架构设计', '模块划分与状态机', C_PRIMARY),
    ('06', '技术实现', '物理引擎 · Canvas矢量绘制', C_SECONDARY),
    ('07', '问题与解决', '开发难点与方案', C_ACCENT),
    ('08', '总结与展望', '成果回顾与未来计划', C_GREEN),
]

for i, (num, title, desc, color) in enumerate(items):
    col = i % 2
    row = i // 2
    x = Inches(0.8) + col * Inches(6.2)
    y = Inches(1.6) + row * Inches(1.35)
    add_round_rect(s, x, y, Inches(5.8), Inches(1.15), C_WHITE)
    add_oval(s, x + Inches(0.15), y + Inches(0.2), Inches(0.75), Inches(0.75), color)
    add_text(s, x + Inches(0.15), y + Inches(0.2), Inches(0.75), Inches(0.75),
             num, size=20, color=C_WHITE, bold=True, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, x + Inches(1.1), y + Inches(0.15), Inches(4.5), Inches(0.5),
             title, size=18, color=C_DARK, bold=True)
    add_text(s, x + Inches(1.1), y + Inches(0.6), Inches(4.5), Inches(0.4),
             desc, size=11, color=C_GRAY)
page_num(s, 2, TOTAL)

# ============================================================
# Slide 3: 项目背景
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_LIGHT)
title_bar(s, '项目背景', '招新任务 · 设计灵感')

# 左栏：招新任务
add_round_rect(s, Inches(0.6), Inches(1.5), Inches(5.8), Inches(5.4), C_WHITE)
add_rect(s, Inches(0.6), Inches(1.5), Inches(5.8), Inches(0.6), C_PRIMARY)
add_text(s, Inches(0.8), Inches(1.5), Inches(5.4), Inches(0.6),
         '🎯 招新任务', size=18, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
add_multi_text(s, Inches(0.9), Inches(2.3), Inches(5.2), Inches(4.4), [
    '借助 AI Agent 自主完成一个小项目',
    '方向不限，关注想法、实现与解决问题',
    '于 2026.10.15 前开源至 GitHub',
    '提交：源代码 + 讲解材料 + 仓库链接',
    '需能独立运行、修改、解释并展示作品',
], size=15, line_spacing=1.8)

# 右栏：设计灵感
add_round_rect(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(5.4), C_WHITE)
add_rect(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(0.6), C_SECONDARY)
add_text(s, Inches(7.1), Inches(1.5), Inches(5.4), Inches(0.6),
         '💡 设计灵感', size=18, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
add_multi_text(s, Inches(7.2), Inches(2.3), Inches(5.2), Inches(4.4), [
    '一份桌宠功能需求清单（7 条创意）',
    '点击互动、摸头、拖拽方向力学',
    '声音触发跳舞、天气换装打伞',
    '节日主题（春节鞭炮烟花）',
    '待机学习/看书/睡觉/惊醒',
    '手绘草图定义四方向拖拽物理',
], size=15, line_spacing=1.6)
page_num(s, 3, TOTAL)

# ============================================================
# Slide 4: 功能总览
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_LIGHT)
title_bar(s, '功能总览', '六大核心模块')

modules = [
    ('🐾', '点击互动', '点身体弹表情\n点头部=摸头', C_PRIMARY),
    ('✋', '拖拽力学', '四方向物理动作\n跳跃/飞跃/落体/滑行', C_SECONDARY),
    ('🎵', '声音跳舞', '麦克风检测音量\n自动触发跳舞', C_ACCENT),
    ('🌤', '天气系统', '自动定位+天气\n换装/打伞/季节场景', C_GREEN),
    ('📅', '节日日历', '春节/中秋等主题\n点击放烟花鞭炮', C_PRIMARY),
    ('💤', '待机AI', '学习/看书/睡觉\n点击惊醒', C_SECONDARY),
]

for i, (icon, title, desc, color) in enumerate(modules):
    col = i % 3
    row = i // 3
    x = Inches(0.6) + col * Inches(4.25)
    y = Inches(1.6) + row * Inches(2.85)
    add_round_rect(s, x, y, Inches(3.95), Inches(2.6), C_WHITE)
    add_oval(s, x + Inches(1.35), y + Inches(0.2), Inches(1.25), Inches(1.25), color)
    add_text(s, x + Inches(1.35), y + Inches(0.2), Inches(1.25), Inches(1.25),
             icon, size=32, color=C_WHITE, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, x + Inches(0.2), y + Inches(1.55), Inches(3.55), Inches(0.45),
             title, size=18, color=C_DARK, bold=True, align=PP_ALIGN.CENTER)
    add_multi_text(s, x + Inches(0.3), y + Inches(2.0), Inches(3.35), Inches(0.6),
                   desc.split('\n'), size=12, color=C_GRAY,
                   align=PP_ALIGN.CENTER, line_spacing=1.3)
page_num(s, 4, TOTAL)

# ============================================================
# Slide 5: 核心交互 - 点击 & 拖拽
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_LIGHT)
title_bar(s, '核心交互：点击与拖拽力学', 'Interaction & Drag Physics')

# 左：点击交互
add_round_rect(s, Inches(0.6), Inches(1.5), Inches(4.2), Inches(5.4), C_WHITE)
add_rect(s, Inches(0.6), Inches(1.5), Inches(4.2), Inches(0.55), C_PRIMARY)
add_text(s, Inches(0.8), Inches(1.5), Inches(3.8), Inches(0.55),
         '🐾 点击互动', size=16, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
add_multi_text(s, Inches(0.85), Inches(2.25), Inches(3.7), Inches(4.5), [
    '点身体 → 随机表情气泡',
    '   嘿嘿~ / 哇! / (≧▽≦)',
    '   戳我干嘛~ / 好痒!',
    '',
    '点头部 → 摸头动作',
    '   嗯~ / 舒服~ / 再摸摸~',
    '',
    '点击睡觉的宠物 → 惊醒！',
    '   吓！！醒了>_<',
], size=13, line_spacing=1.5)

# 右：拖拽方向力学（四象限图）
add_round_rect(s, Inches(5.1), Inches(1.5), Inches(7.6), Inches(5.4), C_WHITE)
add_rect(s, Inches(5.1), Inches(1.5), Inches(7.6), Inches(0.55), C_SECONDARY)
add_text(s, Inches(5.3), Inches(1.5), Inches(7.2), Inches(0.55),
         '✋ 拖拽方向力学（对应设计草图）', size=16, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)

# 中心宠物
ccx, ccy = Inches(8.9), Inches(4.4)
add_oval(s, ccx + Inches(-0.35), ccy + Inches(-0.4), Inches(0.7), Inches(0.85), C_PRIMARY)
add_oval(s, ccx + Inches(0.28), ccy + Inches(-0.2), Inches(0.12), Inches(0.12), C_WHITE)

# ① 上
add_round_rect(s, Inches(8.2), Inches(2.25), Inches(1.8), Inches(0.55), C_BG2)
add_text(s, Inches(8.2), Inches(2.25), Inches(1.8), Inches(0.55),
         '① 竖直向上→起跳', size=11, color=C_DARK, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
add_line(s, ccx, ccy + Inches(-0.4), ccx, Inches(2.85), C_PRIMARY, Pt(2))

# ② 斜向上左
add_round_rect(s, Inches(5.5), Inches(2.55), Inches(1.9), Inches(0.55), C_BG2)
add_text(s, Inches(5.5), Inches(2.55), Inches(1.9), Inches(0.55),
         '② 斜向上→飞跃', size=11, color=C_DARK, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
add_line(s, ccx - Inches(0.3), ccy + Inches(-0.3), Inches(6.4), Inches(3.1),
         C_ACCENT, Pt(2))

# ③ 下
add_round_rect(s, Inches(8.2), Inches(6.1), Inches(1.8), Inches(0.55), C_BG2)
add_text(s, Inches(8.2), Inches(6.1), Inches(1.8), Inches(0.55),
         '③ 竖直向下→落体', size=11, color=C_DARK, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
add_line(s, ccx, ccy + Inches(0.45), ccx, Inches(6.05), C_GREEN, Pt(2))

# ④ 斜向下右
add_round_rect(s, Inches(10.5), Inches(5.8), Inches(1.9), Inches(0.55), C_BG2)
add_text(s, Inches(10.5), Inches(5.8), Inches(1.9), Inches(0.55),
         '④ 斜向下→滑行', size=11, color=C_DARK, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
add_line(s, ccx + Inches(0.3), ccy + Inches(0.3), Inches(10.5), Inches(5.75),
         C_SECONDARY, Pt(2))

page_num(s, 5, TOTAL)

# ============================================================
# Slide 6: 环境感知 - 天气 & 声音
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_LIGHT)
title_bar(s, '环境感知：天气与声音', 'Weather & Sound')

# 左：天气系统
add_round_rect(s, Inches(0.6), Inches(1.5), Inches(6.0), Inches(5.4), C_WHITE)
add_rect(s, Inches(0.6), Inches(1.5), Inches(6.0), Inches(0.55), C_GREEN)
add_text(s, Inches(0.8), Inches(1.5), Inches(5.6), Inches(0.55),
         '🌤 天气系统', size=16, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
add_multi_text(s, Inches(0.85), Inches(2.25), Inches(5.5), Inches(4.5), [
    '数据源：ip-api 定位 + open-meteo 天气',
    '   均免费，无需 API Key',
    '',
    '温度换装（4 档）：',
    '   ≥28°C 热天清凉装 / ≥18°C 暖装',
    '   ≥8°C 凉爽装 / <8°C 冬天厚衣',
    '',
    '雨天 → 自动打小伞',
    '大风(>10m/s) → 伞被吹偏',
    '四季场景：沙滩/草坪/奶茶/发抖',
], size=13, line_spacing=1.45)

# 右：声音跳舞
add_round_rect(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(5.4), C_WHITE)
add_rect(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(0.55), C_ACCENT)
add_text(s, Inches(7.1), Inches(1.5), Inches(5.4), Inches(0.55),
         '🎵 声音跳舞', size=16, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
add_multi_text(s, Inches(7.15), Inches(2.25), Inches(5.3), Inches(4.5), [
    '依赖：sounddevice + numpy（可选）',
    '',
    '原理：后台线程持续采样麦克风',
    '   计算 RMS 音量均方根',
    '   超过阈值(0.04) → 触发跳舞',
    '',
    '跳舞动作：挥手 + 摆腿正弦波动',
    '   多段动作循环，声音停止即停',
    '',
    '未装依赖时自动降级关闭',
    '   可右键菜单手动触发跳舞',
], size=13, line_spacing=1.4)
page_num(s, 6, TOTAL)

# ============================================================
# Slide 7: 节日日历 & 待机AI
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_LIGHT)
title_bar(s, '节日日历与待机 AI', 'Calendar & Idle AI')

# 左：节日
add_round_rect(s, Inches(0.6), Inches(1.5), Inches(6.0), Inches(5.4), C_WHITE)
add_rect(s, Inches(0.6), Inches(1.5), Inches(6.0), Inches(0.55), C_PRIMARY)
add_text(s, Inches(0.8), Inches(1.5), Inches(5.6), Inches(0.55),
         '📅 节日日历', size=16, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
add_multi_text(s, Inches(0.85), Inches(2.25), Inches(5.5), Inches(4.5), [
    '内置 2026 主要节日日期表：',
    '   春节 2.17 / 端午 6.19',
    '   中秋 9.25 / 国庆 10.1-3',
    '   元旦 / 圣诞 / 跨年',
    '',
    '春节主题：',
    '   待机显示红包🧧 + 鞭炮🧨',
    '   点击 → 烟花粒子爆炸特效',
    '   24 颗彩色粒子物理飞溅',
    '',
    '不同节日切换不同待机风格',
    '   以食物/装饰变化为主',
], size=12, line_spacing=1.4)

# 右：待机AI
add_round_rect(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(5.4), C_WHITE)
add_rect(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(0.55), C_SECONDARY)
add_text(s, Inches(7.1), Inches(1.5), Inches(5.4), Inches(0.55),
         '💤 待机 AI', size=16, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
add_multi_text(s, Inches(7.15), Inches(2.25), Inches(5.3), Inches(4.5), [
    '闲置 12 秒 → 随机进入待机：',
    '   📖 学习（看书 + 气泡）',
    '   📚 阅读（捧书 + 翻页）',
    '   😴 睡觉（闭眼 @@ + Zzz）',
    '',
    '待机一段时间后 → 可能自动睡着',
    '',
    '交互打断待机：',
    '   点击睡觉的宠物 → 惊醒状态',
    '   O_O 眼睛 + 张嘴 + "吓！！"',
    '   35 帧后恢复 idle',
], size=13, line_spacing=1.4)
page_num(s, 7, TOTAL)

# ============================================================
# Slide 8: 架构设计
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_LIGHT)
title_bar(s, '架构设计', 'Module Architecture')

# 顶层
add_round_rect(s, Inches(4.17), Inches(1.5), Inches(5), Inches(0.7), C_DARK)
add_text(s, Inches(4.17), Inches(1.5), Inches(5), Inches(0.7),
         'DesktopPet 桌宠主体', size=16, color=C_WHITE, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# 连接线
add_line(s, Inches(6.67), Inches(2.2), Inches(2.2), Inches(2.7), C_GRAY, Pt(1.5))
add_line(s, Inches(6.67), Inches(2.2), Inches(6.67), Inches(2.7), C_GRAY, Pt(1.5))
add_line(s, Inches(6.67), Inches(2.2), Inches(11.13), Inches(2.7), C_GRAY, Pt(1.5))

# 三个服务模块
services = [
    (Inches(0.6), 'WeatherService', '天气服务\nIP定位+open-meteo', C_GREEN),
    (Inches(5.17), 'FestivalService', '节日日历\n2026节日日期表', C_PRIMARY),
    (Inches(9.73), 'SoundMonitor', '声音监听\n麦克风RMS检测', C_ACCENT),
]
for x, name, desc, color in services:
    add_round_rect(s, x, Inches(2.7), Inches(3.2), Inches(1.3), C_WHITE)
    add_rect(s, x, Inches(2.7), Inches(3.2), Inches(0.5), color)
    add_text(s, x, Inches(2.7), Inches(3.2), Inches(0.5),
             name, size=14, color=C_WHITE, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_multi_text(s, x + Inches(0.2), Inches(3.3), Inches(2.8), Inches(0.6),
                   desc.split('\n'), size=11, color=C_GRAY,
                   align=PP_ALIGN.CENTER, line_spacing=1.2)

# 连接线到下层
for x in [Inches(2.2), Inches(6.67), Inches(11.13)]:
    add_line(s, x, Inches(4.0), x, Inches(4.5), C_GRAY, Pt(1.5))

# 下层：桌宠内部四大组件
add_round_rect(s, Inches(0.6), Inches(4.5), Inches(12.13), Inches(0.55), C_BG2)
add_text(s, Inches(0.6), Inches(4.5), Inches(12.13), Inches(0.55),
         'DesktopPet 内部组件', size=13, color=C_DARK, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

components = [
    ('状态机', '12 种状态\n自动流转', C_SECONDARY),
    ('物理引擎', '重力+初速度\n着陆检测', C_PRIMARY),
    ('Canvas绘制', '矢量角色\n表情/道具/场景', C_ACCENT),
    ('事件循环', '30fps after()\n鼠标/键盘', C_GREEN),
]
for i, (name, desc, color) in enumerate(components):
    x = Inches(0.8) + i * Inches(3.05)
    add_round_rect(s, x, Inches(5.25), Inches(2.8), Inches(1.55), C_WHITE)
    add_oval(s, x + Inches(0.2), Inches(5.4), Inches(0.5), Inches(0.5), color)
    add_text(s, x + Inches(0.2), Inches(5.4), Inches(0.5), Inches(0.5),
             str(i + 1), size=14, color=C_WHITE, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, x + Inches(0.85), Inches(5.4), Inches(1.8), Inches(0.5),
             name, size=14, color=C_DARK, bold=True,
             anchor=MSO_ANCHOR.MIDDLE)
    add_multi_text(s, x + Inches(0.2), Inches(6.0), Inches(2.4), Inches(0.7),
                   desc.split('\n'), size=10, color=C_GRAY,
                   align=PP_ALIGN.CENTER, line_spacing=1.2)
page_num(s, 8, TOTAL)

# ============================================================
# Slide 9: 技术实现
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_LIGHT)
title_bar(s, '技术实现', 'State Machine · Physics · Canvas')

# 三栏
techs = [
    ('状态机', C_SECONDARY, [
        '12 种状态枚举',
        'idle / happy / pat',
        'drag / jump / leap',
        'fall / slide / dance',
        'study / read / sleep / wake',
        '',
        '每帧 _update_state()',
        '按计时器自动流转',
        '跳跃→落地→idle',
    ]),
    ('物理引擎', C_PRIMARY, [
        '拖拽释放计算方向角',
        'atan2(-dy, dx)',
        '划分四个扇区',
        '',
        '赋初速度 vx / vy',
        '每帧加重力 0.7~0.8',
        '触地(GROUND_Y)归零',
        '滑行摩擦 0.88 衰减',
    ]),
    ('Canvas 矢量绘制', C_ACCENT, [
        '零外部图片素材',
        'create_oval 身体/眼睛',
        'create_arc 嘴巴/表情',
        'create_polygon 耳朵',
        'create_line 四肢/雨丝',
        '',
        '表情靠切换画法',
        '眨眼/闭眼/开心/^/',
        '道具：伞/书/红包/鞭炮',
    ]),
]

for i, (name, color, lines) in enumerate(techs):
    x = Inches(0.6) + i * Inches(4.25)
    add_round_rect(s, x, Inches(1.5), Inches(3.95), Inches(5.4), C_WHITE)
    add_rect(s, x, Inches(1.5), Inches(3.95), Inches(0.55), color)
    add_text(s, x, Inches(1.5), Inches(3.95), Inches(0.55),
             name, size=16, color=C_WHITE, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_multi_text(s, x + Inches(0.25), Inches(2.25), Inches(3.45), Inches(4.5),
                   lines, size=12, line_spacing=1.45)
page_num(s, 9, TOTAL)

# ============================================================
# Slide 10: 问题与解决
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_LIGHT)
title_bar(s, '问题与解决', 'Development Challenges')

problems = [
    ('窗口透明背景跨平台不一致',
     'Windows 用 -transparentcolor 抠色\n非 Windows 降级为浅色背景'),
    ('无外部图片如何表现角色',
     '全部用 Canvas 矢量图形绘制\n表情靠眼睛/嘴巴画法切换'),
    ('拖拽方向如何准确判断',
     'atan2(-dy,dx) 计算角度\n划分四个扇区对应四种动作'),
    ('声音检测依赖可能缺失',
     'try/except 导入，缺失时\nSOUND_AVAILABLE=False 降级'),
    ('天气 API 需要 Key',
     '用 open-meteo（免费无key）\n+ ip-api 定位，均无需注册'),
    ('节日为农历如何处理',
     '预置 2026 农历转公历日期表\n按 (月,日) 元组快速查找'),
]

for i, (q, a) in enumerate(problems):
    col = i % 2
    row = i // 2
    x = Inches(0.6) + col * Inches(6.2)
    y = Inches(1.55) + row * Inches(1.9)
    add_round_rect(s, x, y, Inches(5.95), Inches(1.7), C_WHITE)
    add_rect(s, x, y, Inches(0.1), Inches(1.7), C_PRIMARY)
    add_text(s, x + Inches(0.25), y + Inches(0.12), Inches(5.5), Inches(0.5),
             'Q ' + q, size=13, color=C_DARK, bold=True)
    add_multi_text(s, x + Inches(0.25), y + Inches(0.65), Inches(5.5), Inches(1),
                   ['A  ' + l for l in a.split('\n')], size=12,
                   color=C_GREEN, line_spacing=1.3)
page_num(s, 10, TOTAL)

# ============================================================
# Slide 11: 运行方式
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_LIGHT)
title_bar(s, '运行方式', 'How to Run')

# 左：基础运行
add_round_rect(s, Inches(0.6), Inches(1.5), Inches(5.8), Inches(5.4), C_WHITE)
add_rect(s, Inches(0.6), Inches(1.5), Inches(5.8), Inches(0.55), C_SECONDARY)
add_text(s, Inches(0.8), Inches(1.5), Inches(5.4), Inches(0.55),
         '🚀 基础运行（零依赖）', size=16, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
add_text(s, Inches(0.85), Inches(2.3), Inches(5.3), Inches(0.4),
         '仅需 Python 3.8+ 标准库', size=13, color=C_GRAY)
# 代码块
add_round_rect(s, Inches(0.85), Inches(2.8), Inches(5.3), Inches(1.0), C_DARK)
add_text(s, Inches(1.0), Inches(2.85), Inches(5.0), Inches(0.9),
         'python pet.py', size=16, color=C_GREEN, font='Consolas',
         anchor=MSO_ANCHOR.MIDDLE)
add_multi_text(s, Inches(0.85), Inches(4.1), Inches(5.3), Inches(2.5), [
    '✓ tkinter（内置 GUI 库）',
    '✓ urllib（天气请求）',
    '✓ datetime（节日判断）',
    '✓ math（拖拽角度计算）',
    '',
    '无任何 pip install 即可运行',
], size=13, line_spacing=1.5)

# 右：启用声音 + 操作
add_round_rect(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(5.4), C_WHITE)
add_rect(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(0.55), C_ACCENT)
add_text(s, Inches(7.1), Inches(1.5), Inches(5.4), Inches(0.55),
         '🎵 启用声音跳舞（可选）', size=16, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
add_round_rect(s, Inches(7.15), Inches(2.3), Inches(5.3), Inches(0.7), C_DARK)
add_text(s, Inches(7.3), Inches(2.3), Inches(5.0), Inches(0.7),
         'pip install sounddevice numpy', size=13, color=C_GREEN,
         font='Consolas', anchor=MSO_ANCHOR.MIDDLE)
add_multi_text(s, Inches(7.15), Inches(3.3), Inches(5.3), Inches(3.4), [
    '操作速查：',
    '  左键点身体 → 弹表情',
    '  左键点头部 → 摸头',
    '  按住拖拽 → 方向动作',
    '  点睡觉宠物 → 惊醒',
    '  右键 → 菜单',
    '  Esc → 退出',
], size=13, line_spacing=1.6)
page_num(s, 11, TOTAL)

# ============================================================
# Slide 12: 总结与展望
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_LIGHT)
title_bar(s, '总结与展望', 'Summary & Future')

# 成果
add_round_rect(s, Inches(0.6), Inches(1.5), Inches(6.0), Inches(5.4), C_WHITE)
add_rect(s, Inches(0.6), Inches(1.5), Inches(6.0), Inches(0.55), C_PRIMARY)
add_text(s, Inches(0.8), Inches(1.5), Inches(5.6), Inches(0.55),
         '✅ 项目成果', size=16, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
add_multi_text(s, Inches(0.85), Inches(2.25), Inches(5.5), Inches(4.5), [
    '单文件 pet.py 实现 6 大功能模块',
    '零外部素材，Canvas 矢量全自包含',
    '12 状态状态机 + 物理引擎',
    '天气/节日/声音三大环境感知',
    '可选依赖优雅降级，开箱即用',
    '',
    '技术栈：Python + tkinter',
    '开源协议：MIT License',
    'GitHub：github.com/zhongwang',
], size=14, line_spacing=1.5)

# 展望
add_round_rect(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(5.4), C_WHITE)
add_rect(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(0.55), C_SECONDARY)
add_text(s, Inches(7.1), Inches(1.5), Inches(5.4), Inches(0.55),
         '🔮 未来展望', size=16, color=C_WHITE, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
add_multi_text(s, Inches(7.15), Inches(2.25), Inches(5.3), Inches(4.5), [
    '动作随音乐风格变化（复杂版）',
    '更多节日主题与食物变化',
    '宠物成长系统 / 好感度',
    '自定义角色皮肤导入',
    '系统托盘常驻 + 开机自启',
    '',
    '从一个想法，',
    '到一个属于自己的开源项目。',
    '—— 期待在作品中认识你。',
], size=14, line_spacing=1.5)
page_num(s, 12, TOTAL)

# ============================================================
# Slide 13: 封底
# ============================================================
s = prs.slides.add_slide(BLANK)
add_bg(s, C_DARK)
add_oval(s, Inches(-1), Inches(4), Inches(3.5), Inches(3.5), C_PRIMARY)
add_oval(s, Inches(10.8), Inches(-1.5), Inches(3.5), Inches(3.5), C_SECONDARY)

add_text(s, Inches(1), Inches(2.5), Inches(11.33), Inches(1.2),
         'Thank You', size=48, color=C_WHITE, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
add_text(s, Inches(1), Inches(4.0), Inches(11.33), Inches(0.6),
         '桌面宠物 Desktop Pet', size=22, color=C_PRIMARY,
         align=PP_ALIGN.CENTER)
add_text(s, Inches(1), Inches(4.7), Inches(11.33), Inches(0.5),
         'Python + tkinter · MIT License', size=14, color=C_GRAY,
         align=PP_ALIGN.CENTER)
add_text(s, Inches(1), Inches(5.5), Inches(11.33), Inches(0.5),
         'github.com/zhongwang', size=16, color=C_SECONDARY,
         align=PP_ALIGN.CENTER)

# ============================================================
# 保存
# ============================================================
out = '/workspace/desktop-pet/桌面宠物项目讲解.pptx'
prs.save(out)
print('SAVED:', out)
print('SLIDES:', len(prs.slides._sldIdLst))
