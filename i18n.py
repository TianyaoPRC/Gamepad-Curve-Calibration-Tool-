# -*- coding: utf-8 -*-
"""
国际化（i18n）管理器
支持多语言文件热加载和用户自定义翻译
"""

import os
import json
import hashlib
import shutil
from typing import Dict, Any, Optional


class I18n:
    """多语言管理器"""
    
    def __init__(self, base_dir: str = None, default_lang: str = "zh_CN", is_lang_dir: bool = False):
        """
        初始化国际化管理器
        
        Args:
            base_dir: 应用基础目录（语言文件放在 base_dir/languages/）或直接的语言文件目录
            default_lang: 默认语言代码（e.g., "zh_CN", "en_US"）
            is_lang_dir: 如果为 True，base_dir 直接指向语言文件目录；否则语言文件在 base_dir/languages/
        """
        if base_dir is None:
            base_dir = os.getcwd()
        
        self.base_dir = base_dir
        # 根据 is_lang_dir 参数决定是否追加 /languages/ 路径
        if is_lang_dir:
            self.lang_dir = base_dir
        else:
            self.lang_dir = os.path.join(base_dir, "languages")
        self.default_lang = default_lang
        self.current_lang = default_lang
        
        # 语言数据缓存 {lang_code: {key: value}}
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # 文件哈希跟踪（用于热更新检测）
        self._file_hashes: Dict[str, str] = {}
        
        # 确保 languages 目录存在
        self._ensure_lang_dir()

        # 确保默认的中文/英文模板存在（防止外部目录被删除时无法启动）
        self._bootstrap_default_templates()

    def _bootstrap_default_templates(self) -> None:
        """若外部语言目录缺失文件，则生成完整的默认模板。"""
        missing_codes = [c for c in ("zh_CN", "en_US", "洪荒古言") if not os.path.exists(self._get_lang_file_path(c))]
        if not missing_codes:
            return

        # 优先复用 launcher 中的完整模板生成逻辑，保证文件是完整版本
        try:
            from launcher import _generate_default_language_templates  # type: ignore

            _generate_default_language_templates(self.lang_dir)
            return
        except Exception:
            pass

        # 退路：如果同目录下带有打包的 languages/ 文件夹，则拷贝缺失的文件
        try:
            bundled_lang_dir = os.path.join(os.path.dirname(__file__), "languages")
            if os.path.isdir(bundled_lang_dir):
                for code in missing_codes:
                    src = os.path.join(bundled_lang_dir, f"{code}.json")
                    dst = self._get_lang_file_path(code)
                    if os.path.exists(dst):
                        continue
                    if os.path.exists(src):
                        shutil.copy2(src, dst)
        except Exception:
            # 写入失败时静默，让调用方后续加载时按键名回退
            pass
    
    def _ensure_lang_dir(self):
        """确保语言文件目录存在"""
        try:
            os.makedirs(self.lang_dir, exist_ok=True)
        except Exception:
            pass
    
    def _get_lang_file_path(self, lang_code: str) -> str:
        """获取语言文件路径"""
        return os.path.join(self.lang_dir, f"{lang_code}.json")
    
    def _get_file_hash(self, filepath: str) -> str:
        """计算文件内容的哈希值"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _load_language_file(self, lang_code: str, force: bool = False) -> Dict[str, Any]:
        """
        加载语言文件到缓存
        
        Args:
            lang_code: 语言代码
            force: 强制重新加载（忽略缓存）
        
        Returns:
            语言数据字典，文件不存在或格式错误返回空字典
        """
        filepath = self._get_lang_file_path(lang_code)
        
        # 检查缓存和文件变更
        if not force and lang_code in self._cache:
            current_hash = self._get_file_hash(filepath)
            if current_hash and current_hash == self._file_hashes.get(lang_code):
                return self._cache[lang_code]
        
        if not os.path.exists(filepath):
            return {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新缓存和哈希
            self._cache[lang_code] = data
            self._file_hashes[lang_code] = self._get_file_hash(filepath)
            
            return data
        except Exception:
            return {}
    
    def set_language(self, lang_code: str):
        """
        切换当前语言
        
        Args:
            lang_code: 语言代码（e.g., "zh_CN", "en_US"）
        """
        # 验证语言文件存在（允许不存在，会回退到默认值）
        self.current_lang = lang_code
        # 加载语言文件到缓存
        self._load_language_file(lang_code)
    
    def get_available_languages(self) -> Dict[str, str]:
        """
        获取所有可用语言
        
        Returns:
            {lang_code: lang_display_name} 字典
        """
        available = {}
        try:
            if os.path.exists(self.lang_dir):
                for f in os.listdir(self.lang_dir):
                    if f.endswith('.json'):
                        lang_code = f[:-5]  # 移除 .json
                        data = self._load_language_file(lang_code)
                        display_name = data.get("_language_name", lang_code)
                        available[lang_code] = display_name
        except Exception:
            pass
        
        # 至少要有默认语言
        if self.default_lang not in available:
            available[self.default_lang] = self.default_lang
        
        return available
    
    def check_for_updates(self):
        """
        检查语言文件是否有更新（哈希变化）
        如有变化，重新加载
        
        Returns:
            changed_langs: 有变化的语言列表
        """
        changed = []
        try:
            if os.path.exists(self.lang_dir):
                for f in os.listdir(self.lang_dir):
                    if f.endswith('.json'):
                        lang_code = f[:-5]
                        filepath = self._get_lang_file_path(lang_code)
                        current_hash = self._get_file_hash(filepath)
                        old_hash = self._file_hashes.get(lang_code, "")
                        
                        if current_hash and current_hash != old_hash:
                            changed.append(lang_code)
                            # 重新加载
                            self._load_language_file(lang_code, force=True)
        except Exception:
            pass
        
        return changed
    
    def get(self, key: str, *args, default: str = None, **kwargs) -> str:
        """
        获取翻译文本
        
        支持以下调用方式：
        - i18n.get("app.title")                                    # 简单键值
        - i18n.get("message.count", 5)                            # 位置参数插值
        - i18n.get("message.greeting", name="Alice")             # 命名参数插值
        
        Args:
            key: 翻译键（支持点号分隔的嵌套键，e.g., "ui.button.ok"）
            *args: 位置参数，用于 str.format() 风格的插值
            default: 键不存在时的默认值（默认返回 key 本身）
            **kwargs: 命名参数，用于 str.format() 风格的插值
        
        Returns:
            翻译后的文本，如果不存在则返回 default 或 key
        """
        # 优先从当前语言加载
        data = self._load_language_file(self.current_lang)
        
        # 使用点号分隔符支持嵌套键
        keys = key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
        
        # 如果当前语言未找到，且不是默认语言，则尝试默认语言
        if value is None and self.current_lang != self.default_lang:
            data = self._load_language_file(self.default_lang)
            value = data
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break
        
        # 如果仍未找到，使用默认值或返回 key
        if value is None:
            if default is not None:
                value = default
            else:
                return key
        
        value = str(value)
        
        # 处理字符串插值
        try:
            if args:
                value = value.format(*args)
            elif kwargs:
                value = value.format(**kwargs)
        except Exception:
            pass  # 格式化失败就返回原字符串
        
        return value
    
    def get_dict(self, key_prefix: str) -> Dict[str, Any]:
        """
        获取嵌套字典（e.g., i18n.get_dict("ui.buttons") 返回所有 ui.buttons.* 的键值）
        
        Args:
            key_prefix: 前缀（点号分隔）
        
        Returns:
            嵌套字典
        """
        data = self._load_language_file(self.current_lang)
        
        keys = key_prefix.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return {}
        
        if isinstance(value, dict):
            return value
        return {}
    
    def has_key(self, key: str) -> bool:
        """检查键是否存在"""
        data = self._load_language_file(self.current_lang)
        
        keys = key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return False
        
        return value is not None


# 全局单例（方便在任何地方使用）
_i18n_instance: Optional[I18n] = None


def init_i18n(base_dir: str = None, default_lang: str = "zh_CN", is_lang_dir: bool = True) -> I18n:
    """初始化全局 i18n 实例"""
    global _i18n_instance
    _i18n_instance = I18n(base_dir, default_lang, is_lang_dir)
    return _i18n_instance


def get_i18n() -> I18n:
    """获取全局 i18n 实例"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n()
    return _i18n_instance


def T(key: str, *args, default: str = None, **kwargs) -> str:
    """快捷函数：T(key) 等价于 get_i18n().get(key)"""
    return get_i18n().get(key, *args, default=default, **kwargs)
