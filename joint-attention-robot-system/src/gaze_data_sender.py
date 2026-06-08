import subprocess
import socket
import re
import sys

# --- 設定：UDP通信 ---
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- 設定：ptgazeコマンド ---
# 公式で正常に動いているコマンドをそのまま指定します
CMD = ["ptgaze", "--mode", "eth-xgaze"]

# --- 数値抽出用のパターン（正規表現） ---
# 「pitch: (数値), yaw: (数値)」という文字列を探すためのルール
GAZE_PATTERN = re.compile(r"pitch:\s*([-+]?\d+\.\d+),\s*yaw:\s*([-+]?\d+\.\d+)")

def main():
    try:
        # プロセス起動
        process = subprocess.Popen(
            CMD,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        print(f"ptgaze を起動しました。UDP送信を開始します ({UDP_IP}:{UDP_PORT})")
        print("（Ctrl + C で終了）\n")

        # リアルタイムで行を受信
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            
            # 生ログをそのまま表示（デバッグ用）
            # print(line, end="") 

            # ログの中から「pitch: ..., yaw: ...」の部分を探す
            match = GAZE_PATTERN.search(line)
            if match:
                # 数値を抽出（文字列から数値に変換）
                pitch_val = match.group(1)
                yaw_val = match.group(2)

                # 受信側(ROS側)が期待する「yaw,pitch」の形式でメッセージを作成
                message = f"{yaw_val},{pitch_val}"
                
                try:
                    # UDPで送信
                    sock.sendto(message.encode(), (UDP_IP, UDP_PORT))
                    print(f"Sent gaze data >> Yaw: {yaw_val}, Pitch: {pitch_val}")
                except Exception as e:
                    print(f"UDP送信エラー: {e}")

    except KeyboardInterrupt:
        print("\n停止します。")
        try:
            process.terminate()
        except:
            pass
    except FileNotFoundError:
        print("\n[エラー] ptgaze コマンドが見つかりません。")

if __name__ == "__main__":
    main()
