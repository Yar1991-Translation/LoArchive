"""爬虫任务注册表：task_type -> 运行函数(ctx, params)。"""

from .ao3 import run as run_ao3
from .lofter_author import run_author_img, run_author_txt
from .lofter_collection import run_like_share_tag
from .lofter_single import run_single_img, run_single_txt

TASK_RUNNERS = {
    "single_img": run_single_img,
    "single_txt": run_single_txt,
    "author_img": run_author_img,
    "author_txt": run_author_txt,
    "like_share_tag": run_like_share_tag,
    "ao3": run_ao3,
}
