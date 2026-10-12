# -*- coding: utf-8 -*-
"""
桌面宠物 (Desktop Pet)
=====================
物光创新实验室 2026 招新作品

一个用 Python + tkinter 实现的桌面宠物程序，无需外部图片素材，
全部角色均由 Canvas 矢量图形实时绘制，自包含可运行。

核心功能（对应功能需求清单）：
  1. 点击互动：点身体弹表情，点头部=摸头
  2. 长按拖拽：根据释放方向触发不同动作（竖直向上跳跃 / 斜向上飞跃 /
     竖直向下自由落体+着陆站起 / 斜向下平移）
  3. 声音响应：检测到环境声音/音乐时触发跳舞（可选依赖，无则降级）
  4. 天气系统：自动获取当地天气，按温度换装；雨天打伞；大风被吹到角落；
     按季节切换场景（沙滩/草坪/奶茶/发抖）
  5. 日历节日：不同节日切换主题待机（春节鞭炮烟花可点击爆炸）
  6. 日常待机：随机进入学习/看书/睡觉，点击睡觉中的宠物会惊醒

作者: zhongwang
许可证: MIT
"""

import tkinter as tk
import urllib.request
import urllib.error
import json
import datetime
import math
import random
import threading
import time
import sys
import platform

# ---------- 可选依赖：声音检测 ----------
try:
    import sounddevice as sd
    import numpy as np
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False


# =====================================================================
#  配置
# =====================================================================
WINDOW_W = 220          # 窗口宽
WINDOW_H = 260          # 窗口高
PET_CX = 110            # 角色中心 x
PET_CY = 150            # 角色中心 y
GROUND_Y = 235          # 地面 y 坐标
FRAME_MS = 33            # 动画帧间隔 (~30fps)
IDLE_TIMEOUT = 12       # 无操作多少秒后进入随机待机
WEATHER_INTERVAL = 1800  # 天气刷新间隔(秒)
SOUND_INTERVAL = 1.0    # 声音检测间隔(秒)
SOUND_THRESHOLD = 0.04   # 触发跳舞的声音阈值

# 透明色（Windows 下用 -transparentcolor 抠掉）
TRANS_COLOR = '#abcdef'


# =====================================================================
#  天气服务
# =====================================================================
class WeatherService:
    """获取当地天气（ip-api 定位 + open-meteo 查询，均免费无需 API key）"""

    def __init__(self):
        self.lock = threading.Lock()
        self.data = None  # {'temp':, 'code':, 'wind':, 'is_day':}
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self.running:
            try:
                self._fetch()
            except Exception:
                pass
            time.sleep(WEATHER_INTERVAL)

    def _fetch(self):
        # 1) 用 IP 定位获取经纬度
        lat, lon = 22.5431, 114.0579  # 默认深圳
        try:
            req = urllib.request.Request(
                'http://ip-api.com/json/?fields=lat,lon',
                headers={'User-Agent': 'DesktopPet/1.0'})
            with urllib.request.urlopen(req, timeout=8) as r:
                geo = json.loads(r.read().decode())
                lat, lon = geo['lat'], geo['lon']
        except Exception:
            pass  # 用默认坐标

        # 2) open-meteo 查询天气
        url = ('https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s'
               '&current=temperature_2m,weather_code,wind_speed_10m,is_day'
               % (lat, lon))
        req = urllib.request.Request(url, headers={'User-Agent': 'DesktopPet/1.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = json.loads(r.read().decode())
        cur = raw.get('current', {})
        with self.lock:
            self.data = {
                'temp': cur.get('temperature_2m', 20),
                'code': cur.get('weather_code', 0),
                'wind': cur.get('wind_speed_10m', 0),
                'is_day': cur.get('is_day', 1),
            }

    def get(self):
        with self.lock:
            return dict(self.data) if self.data else None

    def stop(self):
        self.running = False

    # ---- 静态判断工具 ----
    @staticmethod
    def is_raining(code):
        # WMO 天气码：小雨~暴雨、冻雨、阵雨
        return code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67,
                        80, 81, 82, 95, 96, 99)

    @staticmethod
    def is_snow(code):
        return code in (71, 73, 75, 77, 85, 86)

    @staticmethod
    def season():
        m = datetime.date.today().month
        if m in (3, 4, 5):
            return 'spring'
        if m in (6, 7, 8):
            return 'summer'
        if m in (9, 10, 11):
            return 'autumn'
        return 'winter'


# =====================================================================
#  节日 / 日历服务
# =====================================================================
class FestivalService:
    """根据日期判断节日，返回 (名称, 主题)"""

    # 2026 年主要节日（含农历节日固定到公历日期）
    FESTIVALS = {
        (1, 1): ('元旦', 'newyear'),
        (2, 17): ('春节', 'spring'),        # 2026 农历正月初一
        (2, 18): ('春节', 'spring'),
        (2, 19): ('春节', 'spring'),
        (5, 1): ('劳动节', 'labor'),
        (6, 19): ('端午节', 'dragon'),
        (9, 25): ('中秋节', 'midautumn'),
        (10, 1): ('国庆节', 'national'),
        (10, 2): ('国庆节', 'national'),
        (10, 3): ('国庆节', 'national'),
        (12, 25): ('圣诞节', 'christmas'),
        (12, 31): ('跨年', 'newyeareve'),
    }

    @classmethod
    def today(cls):
        d = datetime.date.today()
        return cls.FESTIVALS.get((d.month, d.day), (None, None))


# =====================================================================
#  声音监听（可选）
# =====================================================================
class SoundMonitor:
    """后台监听麦克风音量，超过阈值时通知主线程跳舞"""

    def __init__(self):
        self.enabled = SOUND_AVAILABLE
        self.active = False
        self.running = True
        self._lock = threading.Lock()
        if self.enabled:
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def _loop(self):
        try:
            stream = sd.Stream(blocksize=1024, samplerate=44100,
                               channels=1, dtype='float32')
            stream.start()
        except Exception:
            self.enabled = False
            return
        while self.running:
            try:
                block, _ = stream.read(1024)
                rms = float(np.sqrt(np.mean(block ** 2)))
                with self._lock:
                    self.active = rms > SOUND_THRESHOLD
            except Exception:
                pass
            time.sleep(SOUND_INTERVAL)
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass

    def is_loud(self):
        if not self.enabled:
            return False
        with self._lock:
            return self.active

    def stop(self):
        self.running = False


# =====================================================================
#  桌宠主体
# =====================================================================
class DesktopPet:
    """桌宠主程序：状态机 + Canvas 绘制 + 交互事件"""

    # 状态枚举
    S_IDLE = 'idle'
    S_HAPPY = 'happy'        # 点身体
    S_PAT = 'pat'            # 摸头
    S_DRAG = 'drag'          # 拖拽中
    S_JUMP = 'jump'          # 竖直向上
    S_LEAP = 'leap'          # 斜向上
    S_FALL = 'fall'          # 竖直向下(自由落体)
    S_SLIDE = 'slide'        # 斜向下平移
    S_DANCE = 'dance'        # 跳舞
    S_STUDY = 'study'        # 学习
    S_READ = 'read'          # 看书
    S_SLEEP = 'sleep'        # 睡觉
    S_WAKE = 'wake'          # 惊醒

    # 角色配色（按温度/季节）
    OUTFITS = {
        'hot':   {'body': '#FF8C5A', 'belly': '#FFD8B5'},   # 夏天清凉
        'warm':  {'body': '#FFB347', 'belly': '#FFE0B0'},   # 温暖
        'cool':  {'body': '#7EC8E3', 'belly': '#D4F0FA'},   # 凉爽加衣
        'cold':  {'body': '#6A5ACD', 'belly': '#B0A0E0'},   # 冬天厚衣
    }

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('桌面宠物')
        self.root.geometry('%dx%d+80+80' % (WINDOW_W, WINDOW_H))
        self.root.overrideredirect(True)          # 无边框
        self.root.attributes('-topmost', True)     # 置顶

        # Windows 透明背景；非 Windows 用浅色兜底
        if platform.system() == 'Windows':
            self.root.wm_attributes('-transparentcolor', TRANS_COLOR)
            bg = TRANS_COLOR
        else:
            bg = '#f0f0f0'

        self.canvas = tk.Canvas(self.root, width=WINDOW_W, height=WINDOW_H,
                                bg=bg, highlightthickness=0)
        self.canvas.pack()

        # ---- 运行时状态 ----
        self.state = self.S_IDLE
        self.prev_idle_state = self.S_IDLE
        self.frame = 0                # 全局帧计数
        self.state_timer = 0          # 当前状态持续帧数
        self.last_interaction = time.time()

        # 拖拽
        self.drag_start = None        # (x, y, t)
        self.drag_offset = (0, 0)
        self._drag_moved = False

        # 物理（跳跃/下落）
        self.vy = 0.0
        self.vx = 0.0
        self.pet_x = float(PET_CX)
        self.pet_y = float(PET_CY)
        self.on_ground = True

        # 天气 & 节日
        self.weather = WeatherService()
        self.festival_name, self.festival_theme = FestivalService.today()
        self.sound = SoundMonitor()

        # 表情气泡
        self.bubble_text = ''
        self.bubble_timer = 0

        # 烟花/鞭炮特效
        self.fx_particles = []        # [(x,y,vx,vy,life,color)]

        # 右键菜单
        self._build_menu()

        # 事件绑定
        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_motion)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.root.bind('<Button-3>', self._on_right)
        self.root.bind('<Escape>', lambda e: self.quit())

        # 启动主循环
        self._tick()

    # -----------------------------------------------------------------
    #  右键菜单
    # -----------------------------------------------------------------
    def _build_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label='刷新天气', command=self._refresh_weather)
        self.menu.add_command(label='让它睡觉', command=lambda: self._set_state(self.S_SLEEP))
        self.menu.add_command(label='让它跳舞', command=lambda: self._set_state(self.S_DANCE))
        self.menu.add_separator()
        self.menu.add_command(label='关于', command=self._about)
        self.menu.add_command(label='退出 (Esc)', command=self.quit)

    def _on_right(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def _about(self):
        self._show_bubble('我是桌宠~ Esc退出 右键菜单')

    def _refresh_weather(self):
        threading.Thread(target=self.weather._fetch, daemon=True).start()
        self._show_bubble('天气刷新中...')

    # -----------------------------------------------------------------
    #  鼠标交互
    # -----------------------------------------------------------------
    def _on_press(self, event):
        self.last_interaction = time.time()
        self.drag_start = (event.x, event.y, time.time())
        self._drag_moved = False
        # 若在睡觉则惊醒
        if self.state == self.S_SLEEP:
            self._set_state(self.S_WAKE)
            self._show_bubble('吓！！醒了>_<')
            return

    def _on_motion(self, event):
        if self.drag_start is None:
            return
        sx, sy, _ = self.drag_start
        dx = event.x - sx
        dy = event.y - sy
        if abs(dx) > 3 or abs(dy) > 3:
            self._drag_moved = True
            self._set_state(self.S_DRAG)
            self.drag_offset = (dx, dy)

    def _on_release(self, event):
        if self.drag_start is None:
            return
        sx, sy, st = self.drag_start
        dt = time.time() - st
        dx = event.x - sx
        dy = event.y - sy
        self.drag_start = None
        self.drag_offset = (0, 0)

        # ---- 判断：拖拽释放 vs 点击 ----
        if self._drag_moved and (abs(dx) > 8 or abs(dy) > 8):
            self._handle_drag_release(dx, dy)
        else:
            self._handle_click(event.x, event.y)

    def _handle_click(self, x, y):
        """点击：判断点的是头还是身体"""
        # 春节：点击即放烟花鞭炮
        if self.festival_theme == 'spring':
            self._spawn_firework(self.pet_x, self.pet_y - 30)
            self._show_bubble('砰！新年快乐~')
        head_cy = self.pet_y - 45
        if y < head_cy + 15:
            # 摸头
            self._set_state(self.S_PAT)
            self._show_bubble(random.choice(['嗯~', '舒服~', '再摸摸~']))
        else:
            # 点身体弹表情
            self._set_state(self.S_HAPPY)
            self._show_bubble(random.choice(['嘿嘿~', '哇!', '(≧▽≦)', '戳我干嘛~', '好痒!']))

    def _handle_drag_release(self, dx, dy):
        """根据释放方向决定动作（对应手绘草图①②③④）"""
        angle = math.degrees(math.atan2(-dy, dx))  # y 向下为正，取反
        dist = math.hypot(dx, dy)
        power = min(dist / 120.0, 1.5)

        # ① 竖直向上 (angle ~ 90°±20°)
        if 70 <= angle <= 110:
            self.vy = -14 - 6 * power
            self.vx = 0
            self.on_ground = False
            self._set_state(self.S_JUMP)
            self._show_bubble('起飞!')
        # ② 斜向上 (30°~70° 或 110°~150°)
        elif (30 <= angle < 70) or (110 < angle <= 150):
            sign = 1 if dx > 0 else -1
            self.vy = -11 - 5 * power
            self.vx = sign * (8 + 4 * power)
            self.on_ground = False
            self._set_state(self.S_LEAP)
            self._show_bubble('飞咯~')
        # ③ 竖直向下 (angle ~ -90°±20°，即 -110~-70)
        elif -110 <= angle <= -70:
            self.vy = 2
            self.vx = 0
            self.on_ground = False
            self._set_state(self.S_FALL)
            self._show_bubble('啊——!')
        # ④ 斜向下平移
        else:
            sign = 1 if dx > 0 else -1
            self.vx = sign * (6 + 3 * power)
            self.vy = 0
            self._set_state(self.S_SLIDE)
            self._show_bubble('滑~')

    # -----------------------------------------------------------------
    #  状态管理
    # -----------------------------------------------------------------
    def _set_state(self, s):
        self.state = s
        self.state_timer = 0

    def _show_bubble(self, text):
        self.bubble_text = text
        self.bubble_timer = 90  # 显示约 3 秒

    # -----------------------------------------------------------------
    #  主循环
    # -----------------------------------------------------------------
    def _tick(self):
        self.frame += 1
        self.state_timer += 1

        # 声音检测 -> 跳舞
        if (self.sound.enabled and self.sound.is_loud()
                and self.state in (self.S_IDLE, self.S_STUDY, self.S_READ,
                                   self.S_SLEEP) and self.on_ground):
            self._set_state(self.S_DANCE)
            self._show_bubble('音乐响起~')

        # 各状态更新
        self._update_state()

        # 闲置检测
        if (time.time() - self.last_interaction > IDLE_TIMEOUT
                and self.state in (self.S_IDLE,)
                and self.on_ground):
            self._enter_random_idle()

        # 气泡计时
        if self.bubble_timer > 0:
            self.bubble_timer -= 1

        # 特效粒子
        self._update_particles()

        # 重绘
        self._draw()

        self.root.after(FRAME_MS, self._tick)

    def _update_state(self):
        s = self.state
        t = self.state_timer

        # ---- 短暂表情状态自动回到 IDLE ----
        if s == self.S_HAPPY and t > 45:
            self._set_state(self.S_IDLE)
        elif s == self.S_PAT and t > 50:
            self._set_state(self.S_IDLE)
        elif s == self.S_WAKE and t > 35:
            self._set_state(self.S_IDLE)

        # ---- 物理：跳跃 / 飞跃 / 下落 ----
        elif s == self.S_JUMP:
            self.vy += 0.7  # 重力
            self.pet_y += self.vy
            self.pet_x += self.vx
            self._clamp_x()
            if self.pet_y >= PET_CY:
                self.pet_y = float(PET_CY)
                self.vy = 0
                self.on_ground = True
                self._set_state(self.S_IDLE)
                self._show_bubble('啪！着陆~')
        elif s == self.S_LEAP:
            self.vy += 0.7
            self.pet_y += self.vy
            self.pet_x += self.vx
            self._clamp_x()
            if self.pet_y >= PET_CY:
                self.pet_y = float(PET_CY)
                self.vy = 0
                self.vx = 0
                self.on_ground = True
                self._set_state(self.S_IDLE)
                self._show_bubble('稳稳落地!')
        elif s == self.S_FALL:
            self.vy += 0.8
            self.pet_y += self.vy
            if self.pet_y >= PET_CY:
                self.pet_y = float(PET_CY)
                self.vy = 0
                self.on_ground = True
                self._set_state(self.S_IDLE)
                self._show_bubble('咚! 站起来啦~')
        elif s == self.S_SLIDE:
            self.pet_x += self.vx
            self._clamp_x()
            self.vx *= 0.88
            if abs(self.vx) < 0.3:
                self.vx = 0
                self._set_state(self.S_IDLE)

        # ---- 拖拽中：跟随鼠标 ----
        elif s == self.S_DRAG:
            ox, oy = self.drag_offset
            # 弹性跟随
            target_x = PET_CX + ox
            target_y = PET_CY + oy
            self.pet_x += (target_x - self.pet_x) * 0.35
            self.pet_y += (target_y - self.pet_y) * 0.35
            self.on_ground = False

        # ---- 跳舞：循环若干段动作 ----
        elif s == self.S_DANCE:
            if not (self.sound.enabled and self.sound.is_loud()) and t > 180:
                self._set_state(self.S_IDLE)

        # ---- 待机学习/看书：一段时间后可能睡着 ----
        elif s == self.S_STUDY and t > 600:
            self._set_state(self.S_SLEEP)
        elif s == self.S_READ and t > 600:
            self._set_state(self.S_SLEEP)

    def _clamp_x(self):
        self.pet_x = max(45, min(WINDOW_W - 45, self.pet_x))

    def _enter_random_idle(self):
        self._set_state(random.choice([self.S_STUDY, self.S_READ, self.S_SLEEP]))
        self.last_interaction = time.time()  # 重置以便该状态持续

    # -----------------------------------------------------------------
    #  烟花 / 鞭炮粒子（春节交互）
    # -----------------------------------------------------------------
    def _spawn_firework(self, x, y):
        colors = ['#FF4444', '#FFD700', '#FF69B4', '#00E5FF', '#7CFC00']
        for _ in range(24):
            a = random.uniform(0, math.pi * 2)
            sp = random.uniform(2, 6)
            self.fx_particles.append([
                x, y, math.cos(a) * sp, math.sin(a) * sp - 1,
                random.randint(30, 55), random.choice(colors)])

    def _update_particles(self):
        for p in self.fx_particles:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.15          # 重力
            p[4] -= 1             # 生命
        self.fx_particles = [p for p in self.fx_particles if p[4] > 0]

    # -----------------------------------------------------------------
    #  绘制
    # -----------------------------------------------------------------
    def _draw(self):
        self.canvas.delete('all')
        w = self.weather.get()
        self._draw_scene(w)
        self._draw_pet(w)
        self._draw_particles()
        self._draw_bubble()

    # ---- 场景（天气/季节背景元素）----
    def _draw_scene(self, w):
        season = WeatherService.season()
        # 地面
        self.canvas.create_rectangle(0, GROUND_Y, WINDOW_W, WINDOW_H,
                                     fill='#D9C7A8', outline='')
        # 雨天：雨丝 + 伞
        if w and WeatherService.is_raining(w['code']):
            for i in range(0, WINDOW_W, 18):
                oy = (self.frame * 6 + i) % (WINDOW_H - 20)
                self.canvas.create_line(i, oy, i - 4, oy + 12,
                                         fill='#9CC4D8', dash=(2, 3))
        # 大风：吹偏的痕迹
        if w and w['wind'] > 10:
            for i in range(3):
                yy = 60 + i * 40
                xx = (self.frame * 8 + i * 50) % (WINDOW_W + 60) - 30
                self.canvas.create_text(xx, yy, text='~', fill='#ccc',
                                        font=('Arial', 14))

        # 季节场景小元素
        if season == 'summer':
            self.canvas.create_oval(180, 15, 210, 45, fill='#FFD700', outline='')
        elif season == 'spring':
            self.canvas.create_text(190, 30, text='🌸', font=('Arial', 16))
        elif season == 'autumn':
            self.canvas.create_text(190, 30, text='🥤', font=('Arial', 16))
        elif season == 'winter':
            for i in range(5):
                sx = (i * 50 + self.frame // 2) % WINDOW_W
                sy = (i * 40 + self.frame) % (WINDOW_H - 30)
                self.canvas.create_text(sx, sy, text='❄', fill='#B0D8FF',
                                        font=('Arial', 10))

    # ---- 角色主体 ----
    def _draw_pet(self, w):
        s = self.state
        # 拖拽时整体偏移已计入 pet_x/pet_y
        cx, cy = self.pet_x, self.pet_y

        # 换装
        outfit = self._outfit(w)
        body_c = outfit['body']
        belly_c = outfit['belly']

        # 弹跳压缩（落地瞬间）
        squash = 1.0
        if s == self.S_JUMP and self.on_ground is False and self.vy > -2:
            squash = 0.85
        if s == self.S_FALL and self.pet_y >= PET_CY - 5:
            squash = 0.82

        bw = 60 * squash
        bh = 70 / squash
        # 身体（圆角椭圆）
        self.canvas.create_oval(cx - bw / 2, cy - bh / 2,
                                cx + bw / 2, cy + bh / 2,
                                fill=body_c, outline='#5a3a1a', width=2)
        # 肚皮
        self.canvas.create_oval(cx - 20, cy - 5, cx + 20, cy + 35,
                                fill=belly_c, outline='')

        # 耳朵
        ear_tilt = 0
        if s == self.S_SLEEP:
            ear_tilt = 8
        self._draw_ear(cx - 22, cy - 30, -1, ear_tilt, body_c)
        self._draw_ear(cx + 22, cy - 30, 1, ear_tilt, body_c)

        # 眼睛
        self._draw_eyes(cx, cy, s)

        # 嘴巴
        self._draw_mouth(cx, cy + 12, s)

        # 腮红
        if s in (self.S_HAPPY, self.S_PAT, self.S_DANCE):
            self.canvas.create_oval(cx - 30, cy + 5, cx - 22, cy + 12,
                                    fill='#FF9999', outline='')
            self.canvas.create_oval(cx + 22, cy + 5, cx + 30, cy + 12,
                                    fill='#FF9999', outline='')

        # 四肢
        self._draw_limbs(cx, cy, s)

        # 道具
        self._draw_props(cx, cy, s, w)

    def _outfit(self, w):
        if w:
            t = w['temp']
            if t >= 28:
                return self.OUTFITS['hot']
            if t >= 18:
                return self.OUTFITS['warm']
            if t >= 8:
                return self.OUTFITS['cool']
            return self.OUTFITS['cold']
        return self.OUTFITS['warm']

    def _draw_ear(self, x, y, side, tilt, color):
        pts = [x, y - 18, x - 8 * side, y + tilt, x + 8 * side, y + tilt]
        self.canvas.create_polygon(pts, fill=color, outline='#5a3a1a', width=1.5)

    def _draw_eyes(self, cx, cy, s):
        ex = 16
        ey = cy - 8
        if s == self.S_SLEEP:
            # 闭眼 @@  睡觉
            self.canvas.create_arc(cx - ex - 6, ey - 3, cx - ex + 6, ey + 5,
                                   start=0, extent=180, style='arc', width=2)
            self.canvas.create_arc(cx + ex - 6, ey - 3, cx + ex + 6, ey + 5,
                                   start=0, extent=180, style='arc', width=2)
        elif s == self.S_HAPPY:
            # ^ ^ 开心
            self.canvas.create_text(cx - ex, ey, text='^', font=('Arial', 16))
            self.canvas.create_text(cx + ex, ey, text='^', font=('Arial', 16))
        elif s == self.S_WAKE:
            # 惊醒 O O
            self.canvas.create_oval(cx - ex - 5, ey - 5, cx - ex + 5, ey + 5,
                                   fill='#222', outline='')
            self.canvas.create_oval(cx + ex - 5, ey - 5, cx + ex + 5, ey + 5,
                                   fill='#222', outline='')
        else:
            # 正常圆眼，带眨眼
            blink = (self.frame % 200 < 8) and s == self.S_IDLE
            if blink:
                self.canvas.create_line(cx - ex - 5, ey, cx - ex + 5, ey,
                                        width=2)
                self.canvas.create_line(cx + ex - 5, ey, cx + ex + 5, ey,
                                        width=2)
            else:
                self.canvas.create_oval(cx - ex - 5, ey - 5, cx - ex + 5, ey + 5,
                                       fill='#222', outline='')
                self.canvas.create_oval(cx + ex - 5, ey - 5, cx + ex + 5, ey + 5,
                                       fill='#222', outline='')
                # 高光
                self.canvas.create_oval(cx - ex - 2, ey - 3, cx - ex + 1, ey,
                                       fill='#fff', outline='')
                self.canvas.create_oval(cx + ex - 2, ey - 3, cx + ex + 1, ey,
                                       fill='#fff', outline='')

    def _draw_mouth(self, cx, cy, s):
        if s in (self.S_HAPPY, self.S_PAT, self.S_DANCE):
            self.canvas.create_arc(cx - 10, cy - 4, cx + 10, cy + 12,
                                   start=0, extent=-180, style='chord',
                                   fill='#CC4444', outline='')
        elif s == self.S_SLEEP:
            self.canvas.create_text(cx, cy, text='z', font=('Arial', 10))
            self.canvas.create_text(cx + 12, cy - 10, text='Z',
                                   font=('Arial', 14))
        elif s == self.S_WAKE:
            self.canvas.create_oval(cx - 5, cy - 2, cx + 5, cy + 8,
                                    fill='#662222', outline='')
        else:
            self.canvas.create_line(cx - 6, cy, cx + 6, cy, width=2)

    def _draw_limbs(self, cx, cy, s):
        # 简单手脚
        f = self.frame
        if s == self.S_DANCE:
            # 跳舞挥手
            arm = math.sin(f * 0.3) * 12
            self.canvas.create_line(cx - 25, cy + 5, cx - 38, cy - 10 + arm,
                                     width=5, fill='#5a3a1a')
            self.canvas.create_line(cx + 25, cy + 5, cx + 38, cy - 10 - arm,
                                     width=5, fill='#5a3a1a')
            leg = math.sin(f * 0.3 + 1) * 6
            self.canvas.create_line(cx - 12, cy + 30, cx - 14, cy + 45 + leg,
                                     width=5, fill='#5a3a1a')
            self.canvas.create_line(cx + 12, cy + 30, cx + 14, cy + 45 - leg,
                                     width=5, fill='#5a3a1a')
        elif s == self.S_JUMP:
            self.canvas.create_line(cx - 25, cy + 5, cx - 40, cy - 5,
                                     width=5, fill='#5a3a1a')
            self.canvas.create_line(cx + 25, cy + 5, cx + 40, cy - 5,
                                     width=5, fill='#5a3a1a')
            self.canvas.create_line(cx - 12, cy + 30, cx - 14, cy + 40,
                                     width=5, fill='#5a3a1a')
            self.canvas.create_line(cx + 12, cy + 30, cx + 14, cy + 40,
                                     width=5, fill='#5a3a1a')
        else:
            self.canvas.create_line(cx - 25, cy + 5, cx - 36, cy + 18,
                                     width=5, fill='#5a3a1a')
            self.canvas.create_line(cx + 25, cy + 5, cx + 36, cy + 18,
                                     width=5, fill='#5a3a1a')
            self.canvas.create_line(cx - 12, cy + 30, cx - 14, cy + 48,
                                     width=5, fill='#5a3a1a')
            self.canvas.create_line(cx + 12, cy + 30, cx + 14, cy + 48,
                                     width=5, fill='#5a3a1a')

    def _draw_props(self, cx, cy, s, w):
        # 雨天打伞
        if w and WeatherService.is_raining(w['code']):
            ux = cx
            uy = cy - 55
            self.canvas.create_arc(ux - 35, uy - 5, ux + 35, uy + 25,
                                   start=0, extent=180, fill='#FF6B6B',
                                   outline='#aa3333', width=1)
            self.canvas.create_line(ux, uy, ux, uy + 15, width=2)

        # 学习/看书
        if s == self.S_STUDY or s == self.S_READ:
            self.canvas.create_rectangle(cx - 18, cy + 28, cx + 18, cy + 40,
                                         fill='#FFF8DC', outline='#888')
            self.canvas.create_line(cx - 14, cy + 32, cx + 14, cy + 32, fill='#aaa')
            self.canvas.create_line(cx - 14, cy + 35, cx + 10, cy + 35, fill='#aaa')

        # 睡觉 Zzz 已在 mouth 处理

        # 春节鞭炮/烟花
        if self.festival_theme == 'spring' and s == self.S_IDLE:
            self.canvas.create_text(cx + 30, cy + 30, text='🧨',
                                    font=('Arial', 18))
            # 可点击区域由整体点击处理，这里若点击到鞭炮附近则放烟花
            # （交互在 _handle_click 中：点身体即触发）
        if self.festival_theme == 'spring':
            self.canvas.create_text(cx - 35, cy - 30, text='🧧',
                                    font=('Arial', 16))

    def _draw_particles(self):
        for p in self.fx_particles:
            r = 3 + (p[4] / 55) * 3
            self.canvas.create_oval(p[0] - r, p[1] - r, p[0] + r, p[1] + r,
                                    fill=p[5], outline='')

    def _draw_bubble(self):
        if self.bubble_timer <= 0 or not self.bubble_text:
            return
        x = self.pet_x
        y = self.pet_y - 75
        pad = 6
        # 估算宽度
        w = max(40, len(self.bubble_text) * 12 + pad * 2)
        h = 26
        self.canvas.create_rectangle(x - w / 2, y - h / 2,
                                     x + w / 2, y + h / 2,
                                     fill='white', outline='#999', width=1)
        self.canvas.create_polygon(x - 5, y + h / 2 - 1,
                                   x + 5, y + h / 2 - 1,
                                   x, y + h / 2 + 8,
                                   fill='white', outline='#999')
        self.canvas.create_text(x, y, text=self.bubble_text,
                                font=('Arial', 12))

    # -----------------------------------------------------------------
    #  生命周期
    # -----------------------------------------------------------------
    def run(self):
        self.root.mainloop()

    def quit(self):
        self.weather.stop()
        self.sound.stop()
        self.root.destroy()


# =====================================================================
#  入口
# =====================================================================
if __name__ == '__main__':
    app = DesktopPet()
    try:
        app.run()
    except KeyboardInterrupt:
        app.quit()
