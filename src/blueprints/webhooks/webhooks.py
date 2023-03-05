from flask import Blueprint,session,redirect,url_for,render_template,flash,request,abort,jsonify



webhook_bp = Blueprint("webhooks",__name__,template_folder="templates",static_folder="static")



@webhook_bp.route("/",methods=["POST"])
def github_webhook():
    branch = request.json["ref"].split('/')[-1]
    repo_id = request.json["repository"]["id"]
    latest_commit = request.json["after"]

    return "OK"
    