import logging
from typing import TYPE_CHECKING

from core.file import File, FileType

from .base64_validator import Base64Validator
from .exc import Base64ConversionError

if TYPE_CHECKING:
    from .file_saver import LLMFileSaver

logger = logging.getLogger(__name__)


class Base64ToFileConverter:
    """Base64 字符串到 File 对象转换器"""

    def __init__(self, file_saver: "LLMFileSaver"):
        self.file_saver = file_saver
        self.validator = Base64Validator()

    def convert(self, base64_string: str) -> File:
        """
        将 base64 字符串转换为 File 对象

        Args:
            base64_string: Base64 编码的图片字符串

        Returns:
            File: 转换后的 File 对象

        Raises:
            Base64ConversionError: 转换失败时抛出
        """
        try:
            # 验证并提取图片数据
            image_data, mime_type = self.validator.validate_and_extract(base64_string)

            # 记录日志
            logger.info("Converting base64 string to file: mime_type=%s, size=%d bytes", mime_type, len(image_data))

            # 使用文件保存器保存图片
            file = self.file_saver.save_binary_string(
                data=image_data,
                mime_type=mime_type,
                file_type=FileType.IMAGE,
            )

            logger.info("Successfully converted base64 to file: file_id=%s", file.related_id)

            return file

        except Exception as e:
            logger.exception("Failed to convert base64 string to file")
            raise Base64ConversionError(f"Failed to convert base64 string: {str(e)}")
