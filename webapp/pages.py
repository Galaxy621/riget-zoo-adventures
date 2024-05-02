import markdown2

from flask import Blueprint, render_template, session, request, redirect, url_for
from connector import Connector, Post

bp = Blueprint("pages", __name__)

def redirect_blogs():
    return redirect(url_for("pages.blogs"))

# Checks if the user is an admin
def is_admin(connector: Connector):
    user = session.get("user")
    if not user: return False
    user = connector.get_user_by_id(user["userID"])
    if not user or not user.admin: return False

    return True, user

@bp.route("/")
def index():
    return render_template("index.html.j2")

@bp.route("/admin/<post_id>", methods=["GET"])
def admin(post_id):
    if post_id == '-1':
        return redirect(url_for("pages.create"))
    
    connector = Connector()
    if not is_admin(connector): return "Could not authenticate"

    post = connector.get_post_by_id(post_id)

    return render_template("admin.html.j2", post=post)

@bp.route("/admin/archive/<post_id>")
def archive(post_id):
    connector = Connector()
    isAdmin, user = is_admin(connector)
    if not isAdmin: return "Could not authenticate"

    post = connector.get_post_by_id(post_id)
    if not post: return "Could not find post"

    target = connector.archive_post if not post.unlisted else connector.unarchive_post
    target(post.postID)
    return redirect_blogs()


@bp.route("/admin/delete/<post_id>")
def delete(post_id):
    connector = Connector()
    isAdmin, user = is_admin(connector)
    if not isAdmin: return "Could not authenticate"

    post = connector.get_post_by_id(post_id)
    if not post: return "Could not find post"

    target = connector.query("DELETE FROM `posts` WHERE `posts`.`PostID` = %s;", (post_id,), True)
    return redirect_blogs()

@bp.route("/admin/create", methods = ["GET", "POST"])
def create():
    if request.method == "GET":
        return render_template("admin.html.j2")
    
    connector = Connector()

    isAdmin, user = is_admin(connector)
    if not isAdmin: return "Could not authenticate"
    
    title = request.form.get("title")
    if title is None: return "no title"
    
    contents = request.form.get("contents")
    if contents is None: return "no contents"
    if len(contents.encode("utf-8")) > 4096: return "too big"

    connector.create_post(user, title, contents)
    return "success"

@bp.route("/admin/update/<post_id>", methods=["POST"])
def update(post_id):
    connector = Connector()

    isAdmin, user = is_admin(connector)
    if not isAdmin: return "Could not authenticate"
    
    title = request.form.get("title")
    if title is None: return "no title"
    
    contents = request.form.get("contents")
    if contents is None: return "no contents"
    if len(contents.encode("utf-8")) > 4096: return "too big"

    connector.update_post(post_id, user, title, contents)
    return "success"

# Blogs list page, list all blogs that haven't been archived
@bp.route("/blogs/")
def blogs():
    connector = Connector()
    blogs = connector.query("SELECT * FROM `posts` WHERE Unlisted = 0")
    posts = [Post(*p) for p in blogs]
    posts.sort(reverse=True)
    return render_template("blogs.html.j2", posts = posts)

# Access blog through its ID
@bp.route("/blogs/<post_id>")
def blog(post_id: int):
    connector = Connector()
    post = connector.get_post_by_id(post_id)
    blog_txt = markdown2.markdown(post.contents)
    return render_template("blog.html.j2", post = post, blog_txt = blog_txt)