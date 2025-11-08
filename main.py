# hotkey_demo.py
import time
import pyperclip
import io
import platform
import os
import sys

# 检测当前操作系统
current_os = platform.system()

# 根据操作系统导入相应的模块
if current_os == 'Windows':
    import keyboard
    import win32clipboard
    from PIL import Image
elif current_os == 'Darwin':  # macOS
    try:
        from AppKit import NSPasteboard, NSImage, NSData
        # 使用 Quartz 替代 keyboard 库进行键盘事件模拟
        from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap
        from Quartz import kCGEventKeyDown, kCGEventKeyUp
        # 使用 pynput 替代 keyboard 库进行热键监听
        from pynput import keyboard as pynput_keyboard
        from PIL import Image
    except ImportError as e:
        print(f"错误：在macOS系统上缺少必要的依赖。请运行 'pip install pyobjc pynput Pillow':{e.msg}")
        sys.exit(1)
else:
    print(f"不支持的操作系统: {current_os}")
    sys.exit(1)

from config import DELAY, FONT_FILE, BASEIMAGE_FILE, AUTO_SEND_IMAGE, AUTO_PASTE_IMAGE, BLOCK_HOTKEY, HOTKEY, SEND_HOTKEY,PASTE_HOTKEY,CUT_HOTKEY,SELECT_ALL_HOTKEY,TEXT_BOX_TOPLEFT,IMAGE_BOX_BOTTOMRIGHT,BASE_OVERLAY_FILE,USE_BASE_OVERLAY

from text_fit_draw import draw_text_auto
from image_fit_paste import paste_image_auto

# 自动适配macOS的热键
if current_os == 'Darwin':
    def adapt_hotkey_for_macos(hotkey):
        """在macOS上将热键中的ctrl替换为cmd，将alt替换为opt"""
        if isinstance(hotkey, str):
            # 处理单个热键组合
            adapted = hotkey.lower()
            # 将ctrl替换为cmd
            adapted = adapted.replace('ctrl+', 'cmd+')
            # 将alt替换为opt
            adapted = adapted.replace('alt+', 'opt+')
            # shift键保持不变，但确保它在热键中正确表示
            if 'shift+' in adapted:
                # 已经包含shift，不需要额外处理
                pass
            return adapted
        return hotkey
    
    # 适配所有配置的热键
    HOTKEY = adapt_hotkey_for_macos(HOTKEY)
    SELECT_ALL_HOTKEY = adapt_hotkey_for_macos(SELECT_ALL_HOTKEY)
    CUT_HOTKEY = adapt_hotkey_for_macos(CUT_HOTKEY)
    PASTE_HOTKEY = adapt_hotkey_for_macos(PASTE_HOTKEY)
    SEND_HOTKEY = adapt_hotkey_for_macos(SEND_HOTKEY)

def copy_png_bytes_to_clipboard(png_bytes: bytes):
    if current_os == 'Windows':
        # Windows 剪贴板操作（保持不变）
        image = Image.open(io.BytesIO(png_bytes))
        with io.BytesIO() as output:
            image.convert("RGB").save(output, "BMP")
            bmp_data = output.getvalue()[14:]
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
        win32clipboard.CloseClipboard()
    elif current_os == 'Darwin':
        # macOS 剪贴板操作（保持不变）
        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        ns_data = NSData.dataWithBytes_length_(png_bytes, len(png_bytes))
        pasteboard.setData_forType_(ns_data, "public.png")

def send_keystroke(key_combo):
    """
    跨平台模拟键盘输入
    """
    if current_os == 'Windows':
        keyboard.send(key_combo)
    elif current_os == 'Darwin':
        # macOS 键盘模拟实现
        def press_key(key_code):
            event = CGEventCreateKeyboardEvent(None, key_code, True)
            CGEventPost(kCGHIDEventTap, event)
            # 添加小延时确保按键事件被正确处理
            time.sleep(0.01)
        
        def release_key(key_code):
            event = CGEventCreateKeyboardEvent(None, key_code, False)
            CGEventPost(kCGHIDEventTap, event)
            # 添加小延时确保按键事件被正确处理
            time.sleep(0.01)
        
        # 手动定义macOS键盘键码
        kVK_ANSI_A = 0x00
        kVK_ANSI_C = 0x08
        kVK_ANSI_V = 0x09
        kVK_ANSI_X = 0x07
        kVK_Return = 0x24
        kVK_Command = 0x37
        kVK_Control = 0x3B  # 实际的Control键码，虽然我们通常用Command替代
        kVK_Option = 0x3A  # Option键码，对应Windows的Alt键
        kVK_Shift = 0x38   # Shift键码
        kVK_ANSI_Z = 0x06  # 添加更多常用键的支持
        kVK_ANSI_S = 0x01  # S键
        kVK_ANSI_D = 0x02  # D键
        kVK_ANSI_F = 0x03  # F键
        kVK_Delete = 0x75  # Delete键
        kVK_Backspace = 0x33  # Backspace键
        kVK_Escape = 0x35    # Escape键
        kVK_Tab = 0x30       # Tab键
        kVK_Space = 0x31     # Space键
        kVK_UpArrow = 0x7E   # 上箭头
        kVK_DownArrow = 0x7D # 下箭头
        kVK_LeftArrow = 0x7B # 左箭头
        kVK_RightArrow = 0x7C # 右箭头
        
        # 解析热键组合，支持多个修饰键
        key_combo = key_combo.lower()
        
        # 记录所有需要按下的修饰键
        pressed_modifiers = []
        
        # 检查并提取修饰键
        if 'cmd+' in key_combo:
            pressed_modifiers.append(kVK_Command)
            key_combo = key_combo.replace('cmd+', '')
        
        if 'ctrl+' in key_combo:
            pressed_modifiers.append(kVK_Control)
            key_combo = key_combo.replace('ctrl+', '')
        
        if 'opt+' in key_combo:
            pressed_modifiers.append(kVK_Option)
            key_combo = key_combo.replace('opt+', '')
        
        if 'shift+' in key_combo:
            pressed_modifiers.append(kVK_Shift)
            key_combo = key_combo.replace('shift+', '')
        
        # 现在key_combo应该只剩下主键了
        main_key = key_combo.strip()
        
        # 扩展热键映射表，添加更多常用键
        key_map = {
            'a': kVK_ANSI_A,
            'c': kVK_ANSI_C,
            'v': kVK_ANSI_V,
            'x': kVK_ANSI_X,
            'z': kVK_ANSI_Z,
            's': kVK_ANSI_S,
            'd': kVK_ANSI_D,
            'f': kVK_ANSI_F,
            'enter': kVK_Return,
            'delete': kVK_Delete,
            'backspace': kVK_Backspace,
            'esc': kVK_Escape,
            'escape': kVK_Escape,
            'tab': kVK_Tab,
            'space': kVK_Space,
            'up': kVK_UpArrow,
            'down': kVK_DownArrow,
            'left': kVK_LeftArrow,
            'right': kVK_RightArrow
        }
        
        if main_key in key_map:
            key_code = key_map[main_key]
            
            # 按顺序按下所有修饰键
            for modifier_key in pressed_modifiers:
                press_key(modifier_key)
            
            # 按下目标键
            press_key(key_code)
            
            # 短暂延迟确保系统识别到组合键
            time.sleep(0.05)
            
            # 释放目标键
            release_key(key_code)
            
            # 按相反顺序释放所有修饰键
            for modifier_key in reversed(pressed_modifiers):
                release_key(modifier_key)
            
            time.sleep(DELAY)
        else:
            print(f"警告：不支持的热键组合 '{key_combo}' 在macOS上")

def cut_all_and_get_text() -> str:
    """
    模拟全选/剪切全部文本，并返回剪切得到的内容。
    """
    # 备份原剪贴板
    old_clip = pyperclip.paste()

    # 清空剪贴板，防止读到旧数据
    pyperclip.copy("")

    # 发送全选和剪切快捷键（使用跨平台函数）
    send_keystroke(SELECT_ALL_HOTKEY)
    send_keystroke(CUT_HOTKEY)
    time.sleep(DELAY)

    # 获取剪切后的内容
    new_clip = pyperclip.paste()

    return new_clip

def try_get_image() -> Image.Image | None:
    """
    尝试从剪贴板获取图像，如果没有图像则返回 None。
    支持 Windows 和 macOS。
    """
    if current_os == 'Windows':
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                if data:
                    # 将 DIB 数据转换为字节流，供 Pillow 打开
                    bmp_data = data
                    # DIB 格式缺少 BMP 文件头，需要手动加上
                    # BMP 文件头是 14 字节，包含 "BM" 标识和文件大小信息
                    header = b'BM' + (len(bmp_data) + 14).to_bytes(4, 'little') + b'\x00\x00\x00\x00\x36\x00\x00\x00'
                    image = Image.open(io.BytesIO(header + bmp_data))
                    return image
        except Exception as e:
            print("无法从剪贴板获取图像：", e)
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
    elif current_os == 'Darwin':
        try:
            # 使用 pyperclip 尝试从剪贴板获取图像
            # 注意：pyperclip 本身不直接支持图像，但我们可以尝试其他方法
            pasteboard = NSPasteboard.generalPasteboard()
            
            # 检查剪贴板中是否有图像数据
            for type in pasteboard.types():
                if "image" in type.lower() or type == "public.png" or type == "public.tiff":
                    # 尝试获取图像数据
                    data = pasteboard.dataForType_(type)
                    if data:
                        # 将 NSData 转换为 bytes
                        png_bytes = data.bytes().tobytes()
                        return Image.open(io.BytesIO(png_bytes))
            
            # 尝试使用 PIL 的 ImageGrab（需要 pyscreenshot 或类似库）
            try:
                from PIL import ImageGrab
                return ImageGrab.grabclipboard()
            except:
                pass
        except Exception as e:
            print("无法从剪贴板获取图像：", e)
    return None

def Start():
    print("Start generate...")

    text=cut_all_and_get_text()
    image=try_get_image()

    if text == "" and image is None:
        print("no text or image")
        return
    
    png_bytes=None

    if image is not None:
        print("Get image")

        try:
            png_bytes = paste_image_auto(
                image_source=BASEIMAGE_FILE,
                image_overlay= BASE_OVERLAY_FILE if USE_BASE_OVERLAY else None,
                top_left=TEXT_BOX_TOPLEFT,
                bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                content_image=image,
                align="center",
                valign="middle",
                padding=12,
                allow_upscale=True, 
                keep_alpha=True,      # 使用内容图 alpha 作为蒙版
                )
        except Exception as e:
            print("Generate image failed:", e)
            return
    
    elif text != "":
        print("Get text: "+text)

        try:
            png_bytes = draw_text_auto(
                image_source=BASEIMAGE_FILE,
                image_overlay= BASE_OVERLAY_FILE if USE_BASE_OVERLAY else None,
                top_left=TEXT_BOX_TOPLEFT,
                bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                text=text,
                color=(0, 0, 0),
                max_font_height=64,        # 例如限制最大字号高度为 64 像素
                font_path=FONT_FILE,
                )
        except Exception as e:
            print("Generate image failed:", e)
            return
        
    if png_bytes is None:
        print("Generate image failed!")
        return
    
    copy_png_bytes_to_clipboard(png_bytes)
    
    if AUTO_PASTE_IMAGE:
        send_keystroke(PASTE_HOTKEY)  # 使用跨平台函数

        time.sleep(DELAY)

        if AUTO_SEND_IMAGE:
            send_keystroke(SEND_HOTKEY)  # 使用跨平台函数

    
    print("Generate image successed!")

# 修改热键监听部分，确保正确处理HOTKEY
if __name__ == "__main__":
    # 在macOS上检查是否以管理员权限运行
    if current_os == 'Darwin':
        import getpass
        if getpass.getuser() != 'root':
            print("\n重要提示：")
            print("在macOS系统上，监听全局键盘事件需要管理员权限。")
            print(f"请使用以下命令以管理员权限运行程序：\n\n  sudo python3 {os.path.abspath(__file__)}")
            print("\n程序将尝试继续运行，但可能无法正常监听热键...\n")
            
    try:
        # 根据操作系统选择不同的热键监听方式
        if current_os == 'Windows':
            # Windows 使用原有的 keyboard 库
            ok = keyboard.add_hotkey(HOTKEY, Start, suppress=BLOCK_HOTKEY or HOTKEY==SEND_HOTKEY)
            print("Starting...")
            print(f"Hot key bind: {str(bool(ok))}")
            print(f"监听热键: {HOTKEY}")
            keyboard.wait()
        elif current_os == 'Darwin':
            # macOS 使用 pynput 库
            print("Starting...")
            print(f"监听热键: {HOTKEY}")
            print("请按下热键来触发功能...")
            
            # 更强大的热键解析器，支持多个修饰键组合
            def parse_hotkey(hotkey_str):
                """解析热键字符串为修饰键和主键"""
                parts = hotkey_str.split('+')
                if len(parts) == 1:
                    return set(), parts[0].strip()
                else:
                    modifiers = set(parts[:-1])
                    main_key = parts[-1].strip()
                    return modifiers, main_key
            
            required_modifiers, target_main_key = parse_hotkey(HOTKEY.lower())
            print(f"热键解析结果: 修饰键={required_modifiers}, 主键={target_main_key}")
            
            # 记录当前按下的修饰键
            pressed_modifiers = set()
            
            def on_press(key):
                try:
                    # 处理修饰键
                    if key == pynput_keyboard.Key.cmd or key == pynput_keyboard.Key.cmd_l or key == pynput_keyboard.Key.cmd_r:
                        pressed_modifiers.add('cmd')
                        print(f"按下修饰键: cmd, 当前按下的修饰键: {pressed_modifiers}")
                    elif key == pynput_keyboard.Key.ctrl or key == pynput_keyboard.Key.ctrl_l or key == pynput_keyboard.Key.ctrl_r:
                        pressed_modifiers.add('ctrl')
                        print(f"按下修饰键: ctrl, 当前按下的修饰键: {pressed_modifiers}")
                    elif key == pynput_keyboard.Key.alt or key == pynput_keyboard.Key.alt_l or key == pynput_keyboard.Key.alt_r:
                        pressed_modifiers.add('opt')  # 在macOS上，Alt就是Option
                        print(f"按下修饰键: opt, 当前按下的修饰键: {pressed_modifiers}")
                    elif key == pynput_keyboard.Key.shift or key == pynput_keyboard.Key.shift_l or key == pynput_keyboard.Key.shift_r:
                        pressed_modifiers.add('shift')
                        print(f"按下修饰键: shift, 当前按下的修饰键: {pressed_modifiers}")
                    
                    # 检查是否匹配热键组合
                    # 特殊处理回车键
                    if key == pynput_keyboard.Key.enter:
                        current_key_name = 'enter'
                        print(f"按下特殊键: {current_key_name}")
                        
                        # 检查是否是目标主键
                        if current_key_name == target_main_key:
                            # 处理macOS上的修饰键兼容性
                            adjusted_modifiers = required_modifiers.copy()
                            
                            # 处理ctrl与cmd的兼容性
                            if 'ctrl' in adjusted_modifiers and 'cmd' in pressed_modifiers:
                                adjusted_modifiers.remove('ctrl')
                                print("macOS兼容模式: 将ctrl要求替换为cmd")
                            
                            # 处理alt与opt的兼容性
                            if 'alt' in adjusted_modifiers:
                                adjusted_modifiers.remove('alt')
                                adjusted_modifiers.add('opt')
                                print("macOS兼容模式: 将alt要求替换为opt")
                            
                            # 检查修饰键是否匹配
                            print(f"检查修饰键: 需要={adjusted_modifiers}, 当前按下={pressed_modifiers}")
                            if adjusted_modifiers.issubset(pressed_modifiers):
                                print(f"检测到匹配的热键组合: {pressed_modifiers}+{current_key_name}, 触发Start()")
                                Start()
                    # 处理字符键
                    elif hasattr(key, 'char') and key.char is not None:
                        key_char = key.char.lower()
                        print(f"按下字符键: {key_char}")
                        
                        # 检查是否是目标主键
                        if key_char == target_main_key:
                            # 处理macOS上ctrl与cmd的兼容性
                            adjusted_modifiers = required_modifiers.copy()
                            if 'ctrl' in adjusted_modifiers and 'cmd' in pressed_modifiers:
                                adjusted_modifiers.remove('ctrl')
                                print("macOS兼容模式: 将ctrl要求替换为cmd")
                            
                            # 同时支持opt和alt键名
                            if 'alt' in adjusted_modifiers:
                                adjusted_modifiers.remove('alt')
                                adjusted_modifiers.add('opt')
                                print("macOS兼容模式: 将alt要求替换为opt")
                            
                            # 检查是否所有必要的修饰键都已按下
                            print(f"检查修饰键: 需要={adjusted_modifiers}, 当前按下={pressed_modifiers}")
                            if adjusted_modifiers.issubset(pressed_modifiers):
                                print(f"检测到匹配的热键组合: {pressed_modifiers}+{key_char}, 触发Start()")
                                Start()
                except Exception as e:
                    print(f"热键处理错误: {e}", exc_info=True)
            
            def on_release(key):
                try:
                    # 释放修饰键
                    if key == pynput_keyboard.Key.cmd or key == pynput_keyboard.Key.cmd_l or key == pynput_keyboard.Key.cmd_r:
                        pressed_modifiers.discard('cmd')
                        print(f"释放修饰键: cmd, 当前按下的修饰键: {pressed_modifiers}")
                    elif key == pynput_keyboard.Key.ctrl or key == pynput_keyboard.Key.ctrl_l or key == pynput_keyboard.Key.ctrl_r:
                        pressed_modifiers.discard('ctrl')
                        print(f"释放修饰键: ctrl, 当前按下的修饰键: {pressed_modifiers}")
                    elif key == pynput_keyboard.Key.alt or key == pynput_keyboard.Key.alt_l or key == pynput_keyboard.Key.alt_r:
                        pressed_modifiers.discard('opt')
                        print(f"释放修饰键: opt, 当前按下的修饰键: {pressed_modifiers}")
                    elif key == pynput_keyboard.Key.shift or key == pynput_keyboard.Key.shift_l or key == pynput_keyboard.Key.shift_r:
                        pressed_modifiers.discard('shift')
                        print(f"释放修饰键: shift, 当前按下的修饰键: {pressed_modifiers}")
                except Exception as e:
                    print(f"热键释放处理错误: {e}")
            
            # 启动监听器，同时监听按键按下和释放事件
            with pynput_keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()
            
    except Exception as e:
        print(f"发生错误: {e}", exc_info=True)
    except KeyboardInterrupt:
        print("\n程序已被用户中断。")
    finally:
        print("程序已退出。")