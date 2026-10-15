# -*- coding: utf-8 -*-
"""プレゼンタイマー Ver.3 Python版（Windows向け）
- ベル1〜4（ベル4は8回）
- 各ベル ON/OFF スイッチ
- 0分0秒のベルも開始直後に鳴動
- MP3再生: Windowsでは winmm/MCI を使用
"""
from __future__ import annotations
import ctypes
import json
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

APP = "プレゼンタイマー"
BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
MP3 = os.path.join(BASE, "assets", "bell.mp3")
# 既存のWindows版設定を引き継ぐため、保存先は旧名称を維持する。
CFG = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "UDCタイマー", "settings.json")
os.makedirs(os.path.dirname(CFG), exist_ok=True)

UDC = "#1596b2"; DEEP = "#073b48"; WARN = "#b98b00"; OVER = "#c62828"

def mci(cmd: str) -> None:
    buf = ctypes.create_unicode_buffer(256)
    ctypes.windll.winmm.mciSendStringW(cmd, buf, 255, 0)

def play_mp3_once(volume: float = 0.85) -> None:
    if not os.path.exists(MP3):
        return
    alias = f"bell{int(time.time()*1000)}{threading.get_ident()}"
    try:
        mci(f'open "{MP3}" type mpegvideo alias {alias}')
        mci(f"setaudio {alias} volume to {int(max(0,min(1,volume))*1000)}")
        mci(f"play {alias}")
        time.sleep(1.05)
    finally:
        try: mci(f"close {alias}")
        except Exception: pass

def fmt(sec: int) -> str:
    sec = max(0, int(sec))
    return f"{sec//60:02d}:{sec%60:02d}"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP + " Ver.3")
        self.geometry("1050x760")
        self.configure(bg=UDC)
        self.running = False
        self.elapsed = 0
        self.last = 0.0
        self.total_min = tk.IntVar(value=10)
        self.total_sec = tk.IntVar(value=0)
        self.volume = tk.DoubleVar(value=0.85)
        self.mode = tk.StringVar(value="remaining")
        self.bells = []
        defaults = [(1,8,0,1,True),(2,10,0,2,True),(3,10,30,3,True),(4,11,0,8,True)]
        for n,m,s,c,on in defaults:
            self.bells.append({"n":n,"min":tk.IntVar(value=m),"sec":tk.IntVar(value=s),"count":c,"on":tk.BooleanVar(value=on),"fired":False})
        self._build()
        self.load_settings()
        self.update_display()

    def _build(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", font=("Meiryo", 13, "bold"), padding=8)
        style.configure("TCheckbutton", background=UDC, foreground="white", font=("Meiryo", 12))
        style.configure("TLabel", background=UDC, foreground="white", font=("Meiryo", 12))
        header = tk.Frame(self, bg=UDC); header.pack(fill="x", padx=20, pady=16)
        tk.Label(header, text=APP, bg=UDC, fg="white", font=("Meiryo", 34, "bold")).pack(side="left")
        ttk.Button(header, text="フルスクリーン", command=self.fullscreen).pack(side="right")
        panel = tk.Frame(self, bg=DEEP); panel.pack(fill="x", padx=20, pady=8)
        self.status = tk.Label(panel, text="残り", bg=DEEP, fg="white", font=("Meiryo", 28, "bold")); self.status.pack(pady=(16,0))
        self.time_lbl = tk.Label(panel, text="10:00", bg=DEEP, fg="white", font=("Consolas", 96)); self.time_lbl.pack()
        self.elapsed_lbl = tk.Label(panel, text="経過時間 00:00", bg=DEEP, fg="white", font=("Meiryo", 20)); self.elapsed_lbl.pack(pady=(0,12))
        self.bell_status = tk.Label(panel, text="", bg=DEEP, fg="white", font=("Meiryo", 22, "bold")); self.bell_status.pack(pady=(0,12))
        ctrl = tk.Frame(self, bg=UDC); ctrl.pack(pady=10)
        for txt, cmd in [("開始", self.start), ("停止", self.pause), ("リセット", self.reset), ("手動ベル1", lambda:self.manual(1)), ("手動ベル4", lambda:self.manual(4))]:
            ttk.Button(ctrl, text=txt, command=cmd).pack(side="left", padx=5)
        body = tk.Frame(self, bg=UDC); body.pack(fill="both", expand=True, padx=20, pady=10)
        left = tk.LabelFrame(body, text="基本設定", bg=UDC, fg="white", font=("Meiryo", 14, "bold")); left.pack(side="left", fill="both", expand=True, padx=(0,8))
        right = tk.LabelFrame(body, text="ベル設定", bg=UDC, fg="white", font=("Meiryo", 14, "bold")); right.pack(side="left", fill="both", expand=True, padx=(8,0))
        row = tk.Frame(left, bg=UDC); row.pack(anchor="w", pady=8, padx=12)
        ttk.Label(row, text="発表時間").pack(side="left", padx=8)
        tk.Spinbox(row, from_=0, to=999, width=5, textvariable=self.total_min, font=("Meiryo",14)).pack(side="left"); ttk.Label(row,text="分").pack(side="left")
        tk.Spinbox(row, from_=0, to=59, width=5, textvariable=self.total_sec, font=("Meiryo",14)).pack(side="left"); ttk.Label(row,text="秒").pack(side="left")
        row = tk.Frame(left, bg=UDC); row.pack(anchor="w", pady=8, padx=12)
        ttk.Label(row, text="表示").pack(side="left", padx=8)
        ttk.Combobox(row, values=["remaining","elapsed"], textvariable=self.mode, width=12, state="readonly").pack(side="left")
        row = tk.Frame(left, bg=UDC); row.pack(anchor="w", pady=8, padx=12)
        ttk.Label(row, text="音量").pack(side="left", padx=8)
        ttk.Scale(row, from_=0, to=1, variable=self.volume, orient="horizontal", length=260).pack(side="left")
        row = tk.Frame(left, bg=UDC); row.pack(anchor="w", pady=16, padx=12)
        ttk.Button(row, text="設定反映", command=self.apply).pack(side="left", padx=5)
        ttk.Button(row, text="設定保存", command=self.save_settings).pack(side="left", padx=5)
        for b in self.bells:
            r = tk.Frame(right, bg=UDC); r.pack(anchor="w", pady=7, padx=12)
            ttk.Checkbutton(r, text=f"ベル{b['n']} ON", variable=b["on"], command=self.update_display).pack(side="left", padx=5)
            tk.Spinbox(r, from_=0, to=999, width=5, textvariable=b["min"], font=("Meiryo",13)).pack(side="left"); ttk.Label(r,text="分").pack(side="left")
            tk.Spinbox(r, from_=0, to=59, width=5, textvariable=b["sec"], font=("Meiryo",13)).pack(side="left"); ttk.Label(r,text="秒").pack(side="left")
            ttk.Label(r, text=f"{b['count']}回").pack(side="left", padx=8)
            ttk.Button(r, text="試聴", command=lambda n=b['n']: self.manual(n)).pack(side="left", padx=5)

    def total(self): return int(self.total_min.get())*60 + int(self.total_sec.get())
    def bell_time(self,b): return int(b["min"].get())*60 + int(b["sec"].get())
    def apply(self):
        for b in self.bells: b["fired"] = False
        self.update_display(); self.save_settings()
    def start(self):
        if self.running: return
        self.running = True
        self.last = time.time()
        self.check_bells()
        self.after(250, self.loop)
    def pause(self): self.running = False
    def reset(self):
        self.running = False; self.elapsed = 0
        for b in self.bells: b["fired"] = False
        self.update_display()
    def loop(self):
        if not self.running: return
        now = time.time(); add = int(now - self.last)
        if add > 0:
            self.elapsed += add; self.last += add
            self.check_bells(); self.update_display()
        self.after(250, self.loop)
    def update_display(self):
        rem = self.total() - self.elapsed
        if self.mode.get()=="elapsed":
            self.status.config(text="経過"); self.time_lbl.config(text=fmt(self.elapsed))
        else:
            self.status.config(text="超過" if rem < 0 else "残り"); self.time_lbl.config(text=fmt(rem))
        self.elapsed_lbl.config(text="経過時間 " + fmt(self.elapsed))
        self.configure(bg=OVER if rem < 0 else WARN if rem <= 60 else UDC)
    def check_bells(self):
        for b in self.bells:
            if b["on"].get() and not b["fired"] and self.elapsed >= self.bell_time(b):
                b["fired"] = True; self.ring(b)
    def manual(self, n:int):
        b = next(x for x in self.bells if x["n"]==n); self.ring(b)
    def ring(self,b):
        self.bell_status.config(text=f"ベル{b['n']}：{b['count']}回")
        def worker():
            for _ in range(b["count"]): play_mp3_once(self.volume.get())
            self.after(500, lambda:self.bell_status.config(text=""))
        threading.Thread(target=worker, daemon=True).start()
    def fullscreen(self): self.attributes("-fullscreen", not bool(self.attributes("-fullscreen")))
    def save_settings(self):
        data={"total_min":self.total_min.get(),"total_sec":self.total_sec.get(),"volume":self.volume.get(),"mode":self.mode.get(),"bells":[{"min":b["min"].get(),"sec":b["sec"].get(),"on":b["on"].get()} for b in self.bells]}
        try:
            with open(CFG,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
        except Exception: pass
    def load_settings(self):
        if not os.path.exists(CFG): return
        try:
            with open(CFG,encoding="utf-8") as f: data=json.load(f)
            self.total_min.set(data.get("total_min",10)); self.total_sec.set(data.get("total_sec",0)); self.volume.set(data.get("volume",.85)); self.mode.set(data.get("mode","remaining"))
            for b,d in zip(self.bells,data.get("bells",[])):
                b["min"].set(d.get("min",b["min"].get())); b["sec"].set(d.get("sec",b["sec"].get())); b["on"].set(d.get("on",True))
        except Exception: pass

if __name__ == "__main__":
    App().mainloop()
