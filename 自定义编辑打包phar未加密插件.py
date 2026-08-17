#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import shutil
from pathlib import Path

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def check_php_environment():
    try:
        subprocess.run(["php", "-v"], check=True, capture_output=True)
        result = subprocess.run(
            ["php", "-r", "echo extension_loaded('phar') ? '1' : '0';"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip() == '0':
            print("❌ PHP phar扩展未加载，请执行相应命令启用。")
            return False
        return True
    except Exception as e:
        print(f"❌ PHP环境检查失败: {str(e)}")
        return False

def run_php_command(php_code):
    try:
        result = subprocess.run(
            ["php", "-d", "phar.readonly=0", "-d", "display_errors=1", "-r", php_code],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else "未知错误"
        print(f"❌ PHP执行错误: {error_msg}")
        return None

def extract_phar(phar_path, output_dir):
    try:
        phar_path = os.path.abspath(phar_path).replace('\\', '/')
        output_dir = os.path.abspath(output_dir).replace('\\', '/')
        os.makedirs(output_dir, mode=0o777, exist_ok=True)
        print(f"🔍 正在解压: {phar_path}")

        php_code = f"""
        error_reporting(E_ALL);
        ini_set('display_errors', '1');
        try {{
            $phar = new Phar('{phar_path}');
            $phar->extractTo('{output_dir}', null, true);
            echo '解压成功（标准模式）';
        }} catch (Exception $e) {{
            $phar = new Phar('{phar_path}');
            $it = new RecursiveIteratorIterator($phar);
            foreach ($it as $file) {{
                $relative = ltrim(str_replace('phar://'.basename('{phar_path}'), '', $file), '/');
                $target = rtrim('{output_dir}', '/') . '/' . $relative;
                @mkdir(dirname($target), 0777, true);
                if ($file->isFile()) {{
                    copy($file, $target);
                }}
            }}
            echo '解压成功（兼容模式）';
        }}
        """
        result = run_php_command(php_code)
        if result and "成功" in result:
            print(f"✅ {result}")
            return True
        else:
            print(f"❌ 解压失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 解压过程异常: {str(e)}")
        return False

def build_phar(source_dir, output_phar, stub_file="plugin.yml", custom_stub_path=None):
    """打包文件夹为.phar，若提供custom_stub_path则使用该文件作为Stub"""
    try:
        source_dir = os.path.abspath(source_dir).replace('\\', '/')
        output_phar = os.path.abspath(output_phar).replace('\\', '/')
        
        # 如果未提供自定义stub，则自动检测入口文件
        if not custom_stub_path:
            possible_stubs = ["plugin.yml", "main.php", "src/main.php"]
            for possible_stub in possible_stubs:
                if os.path.exists(f"{source_dir}/{possible_stub}"):
                    stub_file = possible_stub
                    break
            print(f"🔨 正在打包: {source_dir} -> {output_phar}")
            print(f"📌 自动检测入口文件: {stub_file}")
        else:
            print(f"🔨 正在打包: {source_dir} -> {output_phar}")
            print(f"📌 使用自定义 Stub: {custom_stub_path}")

        if os.path.exists(output_phar):
            os.remove(output_phar)

        # 构建PHP代码
        if custom_stub_path:
            # 使用自定义stub，不压缩
            stub_content = open(custom_stub_path, 'r', encoding='utf-8').read()
            php_code = f"""
            error_reporting(E_ALL);
            ini_set('display_errors', '1');
            try {{
                $phar = new Phar('{output_phar}');
                $phar->buildFromDirectory('{source_dir}');
                $phar->setStub('{stub_content}');
                $phar->setSignatureAlgorithm(Phar::SHA1);
                // 不压缩
                echo '打包成功（自定义Stub）';
            }} catch (Exception $e) {{
                echo '打包失败: ' . $e->getMessage();
            }}
            """
        else:
            php_code = f"""
            error_reporting(E_ALL);
            ini_set('display_errors', '1');
            try {{
                $phar = new Phar('{output_phar}');
                $phar->buildFromDirectory('{source_dir}');
                if (file_exists('{source_dir}/{stub_file}')) {{
                    $phar->setStub($phar->createDefaultStub('{stub_file}'));
                }} else {{
                    $phar->setStub('<?php __HALT_COMPILER(); ?>');
                }}
                $phar->setSignatureAlgorithm(Phar::SHA1);
                echo '打包成功';
            }} catch (Exception $e) {{
                echo '打包失败: ' . $e->getMessage();
            }}
            """
        result = run_php_command(php_code)
        if result and "成功" in result:
            print(f"✅ {result}")
            return True
        else:
            print(f"❌ 打包失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 打包过程异常: {str(e)}")
        return False

def extract_stub(original_phar, output_stub_file):
    """从PHAR中提取stub到指定文件"""
    phar_path = os.path.abspath(original_phar).replace('\\', '/')
    stub_path = os.path.abspath(output_stub_file).replace('\\', '/')
    os.makedirs(os.path.dirname(stub_path), exist_ok=True)

    php_code = f"""
    try {{
        $phar = new Phar('{phar_path}');
        $stub = $phar->getStub();
        file_put_contents('{stub_path}', $stub);
        echo 'EXTRACT_OK';
    }} catch (Exception $e) {{
        echo 'EXTRACT_FAIL: ' . $e->getMessage();
    }}
    """
    out, err, code = run_php_with_return(php_code)
    if "EXTRACT_OK" in out:
        print(f"✅ Stub已提取到: {stub_path}")
        return True
    else:
        print(f"❌ 提取Stub失败: {out} {err}")
        return False

def run_php_with_return(php_code):
    try:
        result = subprocess.run(
            ["php", "-d", "phar.readonly=0", "-d", "display_errors=1", "-r", php_code],
            capture_output=True, text=True, encoding='utf-8'
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def repair_core_phar(source_dir, output_phar, stub_file):
    """修复核心PHAR（使用原始stub，不压缩）"""
    src = os.path.abspath(source_dir).replace('\\', '/')
    out = os.path.abspath(output_phar).replace('\\', '/')
    stub = os.path.abspath(stub_file).replace('\\', '/')

    if not os.path.exists(stub_file):
        print(f"❌ stub文件不存在: {stub_file}")
        return False

    if os.path.exists(output_phar):
        os.remove(output_phar)

    exclude_pattern = r"/\.(git|svn)|__pycache__|\.DS_Store|Thumbs\.db|\.idea|\.vscode|temp_repair|core_repair_temp/"

    php_code = f"""
    error_reporting(E_ALL);
    ini_set('display_errors', '1');

    try {{
        $phar = new Phar('{out}');

        $dir = new RecursiveDirectoryIterator('{src}', FilesystemIterator::SKIP_DOTS);
        $filter = new RecursiveCallbackFilterIterator($dir, function($current, $key, $iterator) {{
            $path = $current->getPathname();
            $exclude = '{exclude_pattern}';
            if (preg_match($exclude, $path)) return false;
            return true;
        }});
        $iterator = new RecursiveIteratorIterator($filter);
        $phar->buildFromIterator($iterator, '{src}');

        // 不压缩
        $stub = file_get_contents('{stub}');
        $phar->setStub($stub);
        $phar->setSignatureAlgorithm(Phar::SHA1);

        $count = count($phar);
        $size = filesize('{out}');
        echo "OK|{{$count}}|{{$size}}";
    }} catch (Exception $e) {{
        echo "FAIL: " . $e->getMessage();
    }}
    """
    out_str, err_str, _ = run_php_with_return(php_code)
    if out_str.startswith("OK|"):
        _, count, size = out_str.split("|")
        src_size = get_dir_size(source_dir)
        print(f"✅ 核心PHAR打包成功")
        print(f"   文件数: {count}")
        print(f"   源文件总大小: {src_size/1024:.1f} KB")
        print(f"   输出PHAR大小: {int(size)/1024:.1f} KB")
        return True
    else:
        print(f"❌ 打包失败: {out_str} {err_str}")
        return False

def get_dir_size(path):
    total = 0
    for dp, dn, filenames in os.walk(path):
        for f in filenames:
            total += os.path.getsize(os.path.join(dp, f))
    return total

def extract_phar_manual(original_phar, output_dir):
    """手动解压PHAR（兼容损坏文件）"""
    phar_path = os.path.abspath(original_phar).replace('\\', '/')
    out_path = os.path.abspath(output_dir).replace('\\', '/')
    os.makedirs(out_path, mode=0o777, exist_ok=True)

    php_code = f"""
    error_reporting(E_ALL);
    ini_set('display_errors', '1');

    try {{
        $phar = new Phar('{phar_path}');
        $phar->extractTo('{out_path}', null, true);
        echo 'EXTRACT_OK';
    }} catch (Exception $e1) {{
        try {{
            $phar = new Phar('{phar_path}');
            $baseLen = strlen('phar://{phar_path}/');
            $it = new RecursiveIteratorIterator($phar);
            $ok = 0;
            $fail = 0;
            foreach ($it as $file) {{
                $fullPath = $file->getPathname();
                $relative = substr($fullPath, $baseLen);
                if (empty($relative)) continue;
                $target = rtrim('{out_path}', '/') . '/' . $relative;
                @mkdir(dirname($target), 0777, true);
                if ($file->isFile()) {{
                    try {{
                        copy($fullPath, $target);
                        $ok++;
                    }} catch (Exception $inner) {{
                        $fail++;
                    }}
                }}
            }}
            echo "EXTRACT_PARTIAL|ok={{$ok}}|fail={{$fail}}";
        }} catch (Exception $e2) {{
            echo 'EXTRACT_FAIL: ' . $e2->getMessage();
        }}
    }}
    """
    out_str, err_str, _ = run_php_with_return(php_code)
    if "EXTRACT_OK" in out_str:
        print("✅ 标准解压成功")
        return True
    elif "EXTRACT_PARTIAL" in out_str:
        print(f"⚠️ 部分解压成功（跳过损坏文件）: {out_str}")
        return True
    else:
        print(f"❌ 解压失败: {out_str} {err_str}")
        return False

def select_directory(prompt, must_exist=True):
    while True:
        path = input(prompt).strip()
        if not path:
            print("⚠️ 路径不能为空")
            continue
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        if must_exist and not os.path.exists(path):
            print(f"❌ 路径不存在: {path}")
            continue
        return path

def select_file(prompt, must_exist=True):
    while True:
        path = input(prompt).strip()
        if not path:
            print("⚠️ 路径不能为空")
            continue
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        if must_exist and not os.path.exists(path):
            print(f"❌ 文件不存在: {path}")
            continue
        return path

def show_banner():
    clear_screen()
    print("""
==========================================
   PocketMine 插件/核心管理工具 (v3.1)
==========================================
功能：
1. 解压 .phar 文件
2. 打包文件夹为 .phar（支持自定义Stub）
3. 修复普通损坏的 .phar
4. 修复核心 PHAR（保留原始 Stub）
5. 提取 .phar 的 Stub 到文件
6. 退出
==========================================
""")

def main():
    show_banner()
    if not check_php_environment():
        return

    while True:
        print("\n请选择操作:")
        print("1. 解压.phar文件")
        print("2. 打包文件夹为.phar（支持自定义Stub）")
        print("3. 修复普通损坏的.phar")
        print("4. 修复核心PHAR（保留原始Stub）")
        print("5. 提取.phar的Stub到文件")
        print("6. 退出")

        choice = input("> 请输入选项 (1-6): ").strip()

        if choice == "1":
            phar_path = select_file("> 请输入.phar文件路径: ")
            output_dir = select_directory("> 请输入解压目录（留空为当前目录）: ", must_exist=False) or os.getcwd()
            extract_phar(phar_path, output_dir)

        elif choice == "2":
            source_dir = select_directory("> 请输入插件文件夹路径: ")
            default_name = os.path.basename(source_dir) + ".phar"
            output_name = input(f"> 请输入输出文件名（默认: {default_name}）: ").strip() or default_name
            if not output_name.endswith('.phar'):
                output_name += '.phar'
            output_path = os.path.join(source_dir, output_name)

            # 询问是否使用自定义Stub
            use_custom = input("> 是否使用自定义 Stub？（y/n，默认 n）: ").strip().lower() == 'y'
            custom_stub_path = None
            temp_stub_file = None
            if use_custom:
                original_phar = select_file("> 请输入原始的 .phar 文件（用于提取 Stub）: ")
                temp_stub_file = os.path.join(os.getcwd(), "temp_stub.php")
                if extract_stub(original_phar, temp_stub_file):
                    custom_stub_path = temp_stub_file
                    print(f"✅ Stub 已提取到临时文件: {temp_stub_file}")
                else:
                    print("❌ 提取 Stub 失败，将使用默认方式打包")
                    custom_stub_path = None

            build_phar(source_dir, output_path, custom_stub_path=custom_stub_path)

            # 清理临时stub文件
            if temp_stub_file and os.path.exists(temp_stub_file):
                os.remove(temp_stub_file)
                print("🧹 已删除临时 Stub 文件")

        elif choice == "3":
            phar_path = select_file("> 请输入损坏的.phar文件路径: ")
            temp_dir = os.path.join(os.getcwd(), "temp_repair")
            if extract_phar(phar_path, temp_dir):
                new_phar = os.path.splitext(phar_path)[0] + "_repaired.phar"
                if build_phar(temp_dir, new_phar):
                    print(f"✅ 修复完成，新文件: {new_phar}")
                shutil.rmtree(temp_dir)
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)

        elif choice == "4":
            print("\n--- 修复核心 PHAR ---")
            original_phar = select_file("> 原始（损坏的）核心PHAR路径: ")
            stub_dir = select_directory("> 请输入Stub文件保存目录（留空使用当前目录）: ", must_exist=False) or os.getcwd()
            default_stub_name = os.path.basename(original_phar) + ".stub.php"
            stub_path = os.path.join(stub_dir, default_stub_name)
            stub_path = input(f"> 请输入Stub文件完整路径（默认: {stub_path}）: ").strip() or stub_path

            print("\n🔍 步骤1: 提取原始Stub...")
            if not extract_stub(original_phar, stub_path):
                print("❌ 无法提取Stub，核心PHAR必须有正确的Stub才能运行。")
                continue

            work_dir = os.path.join(os.getcwd(), "core_repair_temp")
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir, ignore_errors=True)
            os.makedirs(work_dir)
            extracted_dir = os.path.join(work_dir, "extracted")

            print("\n🔍 步骤2: 解压PHAR...")
            if not extract_phar_manual(original_phar, extracted_dir):
                shutil.rmtree(work_dir, ignore_errors=True)
                continue
            print(f"✅ 已解压到: {extracted_dir}")

            input("\n💡 如果需要修改核心文件，请在另一个窗口编辑上面目录中的文件。\n   修改完成后按回车继续...")

            print("\n🔍 步骤3: 重新打包核心PHAR...")
            output_name = os.path.splitext(os.path.basename(original_phar))[0] + "_fixed.phar"
            output_path = os.path.join(os.getcwd(), output_name)

            if repair_core_phar(extracted_dir, output_path, stub_path):
                print(f"\n✅ 修复完成: {output_path}")
                print("   请将此文件替换原来的PHAR并测试。")
            else:
                print("\n❌ 修复失败")

            shutil.rmtree(work_dir, ignore_errors=True)

        elif choice == "5":
            phar_path = select_file("> 请输入.phar文件路径: ")
            default_stub_name = os.path.basename(phar_path) + ".stub.php"
            stub_dir = select_directory("> 请输入Stub保存目录（留空为当前目录）: ", must_exist=False) or os.getcwd()
            stub_path = os.path.join(stub_dir, default_stub_name)
            stub_path = input(f"> 请输入Stub文件完整路径（默认: {stub_path}）: ").strip() or stub_path
            extract_stub(phar_path, stub_path)

        elif choice == "6":
            print("👋 感谢使用，再见！")
            break

        else:
            print("❌ 无效选项，请重新输入")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"❌ 程序异常: {str(e)}")