import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import random
import time
import threading
import json
import os

class LotteryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("轻量级随机抽签系统")
        self.root.geometry("650x550")
        self.root.resizable(True, True)
        
        # 初始化变量
        self.lottery_name = tk.StringVar(value="抽奖")
        self.total_samples = tk.IntVar(value=10)
        self.draw_count = tk.IntVar(value=1)
        self.samples = []
        self.is_drawing = False
        self.current_file = None  # 当前保存的文件路径
        
        self.create_widgets()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置行列权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 抽签名称
        ttk.Label(main_frame, text="抽签名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.lottery_name).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 样本总数
        ttk.Label(main_frame, text="样本总数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(main_frame, from_=1, to=1000, textvariable=self.total_samples, 
                   command=self.update_sample_display).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 抽取个数
        ttk.Label(main_frame, text="抽取个数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(main_frame, from_=1, to=100, textvariable=self.draw_count).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 样本输入区域
        ttk.Label(main_frame, text="样本列表 (每行一个):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.sample_text = scrolledtext.ScrolledText(main_frame, width=40, height=10)
        self.sample_text.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, rowspan=2)
        
        # 样本操作按钮框架
        sample_button_frame = ttk.Frame(main_frame)
        sample_button_frame.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        ttk.Button(sample_button_frame, text="自动生成样本", command=self.auto_generate_samples).pack(side=tk.LEFT, padx=2)
        ttk.Button(sample_button_frame, text="保存样本", command=self.save_samples).pack(side=tk.LEFT, padx=2)
        ttk.Button(sample_button_frame, text="加载样本", command=self.load_samples).pack(side=tk.LEFT, padx=2)
        ttk.Button(sample_button_frame, text="清空样本", command=self.clear_samples).pack(side=tk.LEFT, padx=2)
        
        # 当前文件显示
        self.file_label = ttk.Label(main_frame, text="未保存", foreground="gray")
        self.file_label.grid(row=5, column=1, sticky=tk.E, pady=5)
        
        # 进度条框架
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)
        
        # 进度标签
        self.progress_label = ttk.Label(progress_frame, text="准备就绪")
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        # 进度条 - 使用确定模式
        self.progress = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # 进度百分比
        self.progress_percent = ttk.Label(progress_frame, text="0%")
        self.progress_percent.grid(row=1, column=1, padx=5)
        
        # 结果显示
        ttk.Label(main_frame, text="抽签结果:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.result_text = scrolledtext.ScrolledText(main_frame, width=40, height=5, state=tk.DISABLED)
        self.result_text.grid(row=7, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="开始抽签", command=self.start_draw).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="重置", command=self.reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # 配置权重
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        # 初始化样本显示
        self.auto_generate_samples()
        
    def auto_generate_samples(self):
        """自动生成样本"""
        total = self.total_samples.get()
        samples = [f"样本 {i+1}" for i in range(total)]
        
        self.sample_text.delete(1.0, tk.END)
        self.sample_text.insert(1.0, "\n".join(samples))
        self.current_file = None
        self.update_file_label()
        
    def update_sample_display(self):
        """更新样本显示"""
        self.auto_generate_samples()
        
    def get_samples(self):
        """从文本框中获取样本"""
        text = self.sample_text.get(1.0, tk.END).strip()
        samples = [line.strip() for line in text.split('\n') if line.strip()]
        return samples
        
    def save_samples(self):
        """保存样本到文件"""
        samples = self.get_samples()
        if not samples:
            messagebox.showwarning("警告", "没有样本可保存！")
            return
            
        # 如果已经有保存过的文件，直接使用该路径
        if self.current_file:
            file_path = self.current_file
        else:
            # 否则打开文件选择对话框
            file_path = filedialog.asksaveasfilename(
                title="保存样本",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
        if not file_path:  # 用户取消了保存
            return
            
        try:
            # 准备保存的数据
            data = {
                "lottery_name": self.lottery_name.get(),
                "total_samples": self.total_samples.get(),
                "draw_count": self.draw_count.get(),
                "samples": samples
            }
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.current_file = file_path
            self.update_file_label()
            messagebox.showinfo("成功", f"样本已保存到:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存文件时出错:\n{str(e)}")
            
    def load_samples(self):
        """从文件加载样本"""
        file_path = filedialog.askopenfilename(
            title="加载样本",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if not file_path:  # 用户取消了选择
            return
            
        try:
            # 从文件加载数据
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 更新界面
            self.lottery_name.set(data.get("lottery_name", "抽奖"))
            self.total_samples.set(data.get("total_samples", 10))
            self.draw_count.set(data.get("draw_count", 1))
            
            samples = data.get("samples", [])
            self.sample_text.delete(1.0, tk.END)
            self.sample_text.insert(1.0, "\n".join(samples))
            
            self.current_file = file_path
            self.update_file_label()
            
            messagebox.showinfo("成功", f"样本已从文件加载:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载文件时出错:\n{str(e)}")
            
    def clear_samples(self):
        """清空样本"""
        if messagebox.askyesno("确认", "确定要清空所有样本吗？"):
            self.sample_text.delete(1.0, tk.END)
            self.current_file = None
            self.update_file_label()
            
    def update_file_label(self):
        """更新文件标签显示"""
        if self.current_file:
            # 只显示文件名，不显示完整路径
            file_name = os.path.basename(self.current_file)
            self.file_label.config(text=f"已保存: {file_name}", foreground="green")
        else:
            self.file_label.config(text="未保存", foreground="gray")
        
    def start_draw(self):
        """开始抽签"""
        if self.is_drawing:
            return
            
        # 获取样本
        samples = self.get_samples()
        if not samples:
            messagebox.showerror("错误", "样本列表不能为空！")
            return
            
        # 检查抽取个数
        draw_count = self.draw_count.get()
        if draw_count > len(samples):
            messagebox.showerror("错误", f"抽取个数不能超过样本总数！\n样本总数: {len(samples)}")
            return
            
        # 重置进度条
        self.progress['value'] = 0
        self.progress_percent['text'] = "0%"
        self.progress_label['text'] = "抽签中..."
        
        # 开始抽签
        self.is_drawing = True
        
        # 在新线程中执行抽签
        thread = threading.Thread(target=self.perform_draw, args=(samples, draw_count))
        thread.daemon = True
        thread.start()
        
    def update_progress(self, value):
        """更新进度条"""
        self.progress['value'] = value
        self.progress_percent['text'] = f"{int(value)}%"
        
    def perform_draw(self, samples, draw_count):
        """执行抽签逻辑"""
        # 模拟抽签过程 - 分阶段更新进度条
        stages = [
            ("初始化抽签系统...", 10),
            ("洗牌中...", 25),
            ("随机选择中...", 50),
            ("验证结果...", 75),
            ("最终确定...", 95)
        ]
        
        for stage_text, progress_value in stages:
            if not self.is_drawing:
                return
                
            # 更新进度标签和进度条
            self.root.after(0, self.progress_label.config, {'text': stage_text})
            self.root.after(0, self.update_progress, progress_value)
            
            # 模拟处理时间
            time.sleep(0.5 + random.random())
        
        # 随机抽取
        selected = random.sample(samples, draw_count)
        
        # 完成进度条
        self.root.after(0, self.update_progress, 100)
        self.root.after(0, self.progress_label.config, {'text': '抽签完成!'})
        
        # 在主线程中更新UI
        self.root.after(500, self.show_result, selected)
        
    def show_result(self, result):
        """显示抽签结果"""
        self.is_drawing = False
        
        # 更新结果文本框
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        
        lottery_name = self.lottery_name.get()
        self.result_text.insert(1.0, f"{lottery_name}结果:\n\n")
        
        for i, item in enumerate(result, 1):
            self.result_text.insert(tk.END, f"{i}. {item}\n")
            
        self.result_text.config(state=tk.DISABLED)
        
    def reset(self):
        """重置程序"""
        self.is_drawing = False
        self.progress['value'] = 0
        self.progress_percent['text'] = "0%"
        self.progress_label['text'] = "准备就绪"
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = LotteryApp(root)
    root.mainloop()