from flask import Blueprint,session,redirect,url_for,render_template,flash,request,abort,jsonify



webhook_bp = Blueprint("webhooks",__name__,template_folder="templates",static_folder="static")



@webhook_bp.route("/",methods=["POST"])
def github_webhook():
    print(request.json)
    return "OK"