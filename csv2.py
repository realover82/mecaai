#!/usr/bin/env python3
"""
CSV Analyzer GUI Tool
GUI 기반 CSV 파일 분석 툴
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from pathlib import Path
import threading
import io
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

class CSVAnalyzerGUI:
    """CSV 분석기 GUI 클래스"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("CSV 파일 분석 툴")
        self.root.geometry("1200x800")
        
        self.df = None
        self.file_path = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 파일 선택 프레임
        file_frame = ttk.LabelFrame(main_frame, text="파일 선택", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.file_label = ttk.Label(file_frame, text="선택된 파일: 없음")
        self.file_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        ttk.Button(file_frame, text="CSV 파일 선택", command=self.select_file).grid(row=0, column=1)
        ttk.Button(file_frame, text="분석 실행", command=self.run_analysis).grid(row=0, column=2, padx=(10, 0))
        
        # 노트북 (탭) 생성
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 로그 탭
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="분석 로그")
        self.setup_log_tab()
        
        # 그리드 가중치 설정
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def setup_log_tab(self):
        """로그 탭 설정"""
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def log_message(self, message):
        """로그 메시지 추가"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def select_file(self):
        """파일 선택"""
        file_path = filedialog.askopenfilename(
            title="CSV 파일 선택",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            self.file_path = Path(file_path)
            self.file_label.config(text=f"선택된 파일: {self.file_path.name}")
            self.log_message(f"파일 선택됨: {self.file_path}")
    
    def run_analysis(self):
        """분석 실행"""
        if not self.file_path:
            messagebox.showwarning("경고", "먼저 CSV 파일을 선택해주세요.")
            return
        
        self.log_text.delete(1.0, tk.END)  # 로그 초기화
        
        # 별도 스레드에서 분석 실행
        thread = threading.Thread(target=self.run_analysis_logic)
        thread.daemon = True
        thread.start()

    def read_csv_with_dynamic_header(self, file_path):
        """CSV 파일에서 컬럼명이 있는 행을 동적으로 찾아 DataFrame으로 로드하는 함수."""
        try:
            df_temp = pd.read_csv(file_path, header=None, nrows=100)
            
            # 'Pcb' 관련 필드명으로 키워드 수정
            keywords = ['SNumber', 'PcbStartTime', 'PcbMaxIrPwr', 'PcbPass']
            
            header_row = None
            for i, row in df_temp.iterrows():
                row_values = [str(x).strip() for x in row.values if pd.notna(x)]
                
                if all(keyword in row_values for keyword in keywords):
                    header_row = i
                    break
            
            if header_row is not None:
                df = pd.read_csv(file_path, header=header_row)
                return df
            else:
                self.log_message("경고: 컬럼명 행을 찾을 수 없습니다.")
                return None
        except FileNotFoundError:
            self.log_message(f"오류: 파일을 찾을 수 없습니다. 경로를 확인해주세요: {file_path}")
            return None
        except Exception as e:
            self.log_message(f"오류: 파일 로딩 중 예상치 못한 에러가 발생했습니다: {e}")
            return None

    def run_analysis_logic(self):
        """실제 분석 로직"""
        self.log_message("🚀 분석을 시작합니다...")
        
        df = self.read_csv_with_dynamic_header(self.file_path)
        
        if df is None:
            self.log_message("DataFrame 로드에 실패하여 분석을 중단합니다.")
            return

        self.log_message(f"✅ 파일 로드 성공: {df.shape[0]}행 x {df.shape[1]}열")
        
        # 데이터 전처리
        for col in df.columns:
            df[col] = df[col].apply(lambda x: x.strip('="').strip('"') if isinstance(x, str) else x)

        df['PcbStartTime'] = pd.to_datetime(df['PcbStartTime'], errors='coerce')
        df['PassStatusNorm'] = df['PcbPass'].fillna('').astype(str).str.strip().str.upper()

        summary_data = {}

        # 'PcbMaxIrPwr'를 기준으로 그룹화
        for jig, group in df.groupby('PcbMaxIrPwr'):
            if group['PcbStartTime'].dt.date.dropna().empty:
                continue
            
            for d, day_group in group.groupby(group['PcbStartTime'].dt.date):
                if pd.isna(d):
                    continue
                
                date_iso = pd.to_datetime(d).strftime("%Y-%m-%d")

                pass_sns_series = day_group.groupby('SNumber')['PassStatusNorm'].apply(lambda x: 'O' in x.tolist())
                pass_sns = pass_sns_series[pass_sns_series].index.tolist()

                pass_count = (day_group['PassStatusNorm'] == 'O').sum()

                false_defect_df = day_group[(day_group['PassStatusNorm'] == 'X') & (day_group['SNumber'].isin(pass_sns))]
                false_defect_count = false_defect_df.shape[0]
                false_defect_sns = false_defect_df['SNumber'].unique().tolist()

                true_defect_df = day_group[(day_group['PassStatusNorm'] == 'X') & (~day_group['SNumber'].isin(pass_sns))]
                true_defect_count = true_defect_df.shape[0]

                total_test = len(day_group)
                fail_count = false_defect_count + true_defect_count

                rate = 100 * pass_count / total_test if total_test > 0 else 0

                if jig not in summary_data:
                    summary_data[jig] = {}
                summary_data[jig][date_iso] = {
                    'total_test': total_test,
                    'pass': pass_count,
                    'false_defect': false_defect_count,
                    'true_defect': true_defect_count,
                    'fail': fail_count,
                    'pass_rate': f"{rate:.1f}%",
                    'false_defect_sns': false_defect_sns
                }
        
        all_dates = sorted(list(df['PcbStartTime'].dt.date.dropna().unique()))
        kor_date_cols = [f"{d.strftime('%y%m%d')}" for d in all_dates]

        # === 결과 출력 ===
        self.log_message(f"\n리모컨 생산 데이터 분석 리포트\n{'='*60}\n분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        for jig in sorted(summary_data.keys()):
            self.log_message(f"--- 구분({jig}) ---")
            
            report_data = {
                '지표': ['총 테스트 수', 'PASS', '가성불량', '진성불량', 'FAIL']
            }

            for date_iso, date_str in zip([d.strftime('%Y-%m-%d') for d in all_dates], kor_date_cols):
                data_point = summary_data[jig].get(date_iso)
                if data_point:
                    report_data[date_str] = [
                        data_point['total_test'],
                        data_point['pass'],
                        data_point['false_defect'],
                        data_point['true_defect'],
                        data_point['fail']
                    ]
                else:
                    report_data[date_str] = ['N/A'] * 5
            
            report_df = pd.DataFrame(report_data)
            self.log_message(report_df.to_markdown(index=False))
            self.log_message("")

            for date_iso, date_str in zip([d.strftime('%Y-%m-%d') for d in all_dates], kor_date_cols):
                data_point = summary_data[jig].get(date_iso)
                if data_point and data_point['false_defect_sns']:
                    self.log_message(f"({date_str}) 가성불량 시리얼 번호 목록 ({jig})")
                    for sn in data_point['false_defect_sns']:
                        self.log_message(f"      {sn}")
                    self.log_message("")

            self.log_message("\n" + "="*80 + "\n")

        self.log_message(f"✅ 분석이 완료되었습니다!")

def main():
    """메인 함수"""
    root = tk.Tk()
    app = CSVAnalyzerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
