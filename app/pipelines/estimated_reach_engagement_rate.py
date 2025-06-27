from flask import Flask, request, jsonify
from db.db_ops import db_manager
app = Flask(__name__)

def calculate_metrics(followers, likes, comments, reach_rate=0.35):
    try:
        followers = int(followers)

        if not isinstance(likes, list) or not isinstance(comments, list):
            return {"status": "failed", "error": "Likes and comments must be lists"}, 400

        likes = [int(l) for l in likes]
        comments = [int(c) for c in comments]

        avg_likes = sum(likes) / len(likes) if likes else 0
        avg_comments = sum(comments) / len(comments) if comments else 0

        if followers <= 0:
            return {"status": "failed", "error": "Invalid follower count"}, 400

        engagement_rate = ((avg_likes + avg_comments) / followers) * 100
        estimated_reach = followers * reach_rate
        data = {
            "engagement_rate": engagement_rate,
            "estimated_reach": estimated_reach
        }
        db_manager.insert_data("src_influencer_data_demo", data)
        return {
            "status": "success",
            "total_likes": likes,
            "total_comments": comments,
            "engagement_rate": round(engagement_rate, 2),
            "estimated_reach": int(estimated_reach)
        }, 200

    except Exception as e:
        return {"status": "failed", "error": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
