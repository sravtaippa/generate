from flask import Flask, request, jsonify

app = Flask(__name__)

def calculate_metrics(followers, likes, comments, reach_rate=0.20):
    try:
        # Convert values to integers in case they're passed as strings
        followers = int(followers)
        likes = [int(l) for l in likes]
        comments = [int(c) for c in comments]

        total_likes = sum(likes)
        total_comments = sum(comments)

        if followers <= 0:
            return {"status": "failed", "error": "Invalid follower count"}, 400

        engagement_rate = ((total_likes + total_comments) / followers) * 100
        estimated_reach = followers * reach_rate

        return {
            "status": "success",
            "total_likes": total_likes,
            "total_comments": total_comments,
            "engagement_rate": round(engagement_rate, 2),
            "estimated_reach": int(estimated_reach)
        }

    except Exception as e:
        return {"status": "failed", "error": str(e)}, 500



if __name__ == '__main__':
    app.run(debug=True)
