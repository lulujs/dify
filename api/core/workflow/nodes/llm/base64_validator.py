import base64
import imghdr
import re

from .exc import Base64ValidationError


class Base64Validator:
    """Base64 图片字符串验证器"""

    # 支持的图片格式
    SUPPORTED_IMAGE_FORMATS: set[str] = {"jpeg", "png", "gif", "webp", "bmp"}

    # Data URI scheme 正则表达式
    DATA_URI_PATTERN: re.Pattern[str] = re.compile(r"^data:image/(jpeg|png|gif|webp|bmp);base64,(.+)", re.IGNORECASE)

    @classmethod
    def validate_and_extract(cls, base64_string: str) -> tuple[bytes, str] | None:
        """
        验证 base64 字符串并提取图片数据

        Args:
            base64_string: Base64 编码的图片字符串（可能包含 data URI scheme）

        Returns:
            tuple[bytes, str] | None: (图片二进制数据, MIME 类型) 或 None（当字符串为空时）

        Raises:
            Base64ValidationError: 验证失败时抛出
        """
        # 允许空字符串，返回 None
        if not base64_string or not base64_string.strip():
            return None

        # 去除首尾空白字符
        base64_string = base64_string.strip()

        # 检查是否包含 data URI scheme
        mime_type = None
        match = cls.DATA_URI_PATTERN.match(base64_string)
        if match:
            image_format = match.group(1).lower()
            base64_data = match.group(2)
            mime_type = f"image/{image_format}"
        else:
            base64_data = base64_string

        # 验证 base64 格式
        try:
            image_data = base64.b64decode(base64_data, validate=True)
        except Exception as e:
            raise Base64ValidationError(f"Invalid base64 encoding: {str(e)}")

        # 验证是否为有效图片
        detected_format = imghdr.what(None, h=image_data)
        if detected_format not in cls.SUPPORTED_IMAGE_FORMATS:
            supported_formats = ", ".join(cls.SUPPORTED_IMAGE_FORMATS)
            raise Base64ValidationError(
                f"Unsupported image format. Detected: {detected_format}, Supported: {supported_formats}"
            )

        # 如果没有从 data URI 中提取 MIME 类型，则使用检测到的格式
        if mime_type is None:
            mime_type = f"image/{detected_format}"

        return image_data, mime_type
