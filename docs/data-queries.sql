-- ==========================================================
-- DANH SÁCH CÁC CÂU TRUY VẤN KIỂM TRA DỮ LIỆU (DATA VERIFICATION)
-- Dự án: Youtube Sentiment Datalakehouse - Nhóm 19
-- ==========================================================

-- 1. KIỂM TRA CẤU TRÚC HỆ THỐNG
-- ----------------------------------------------------------
-- Xem danh sách Database
SHOW DATABASES;

-- Chọn database để làm việc
USE lakehouse;

-- Xem danh sách bảng
SHOW TABLES;

-- Xem chi tiết bảng Silver
DESCRIBE lakehouse.silver_youtube_comments;


-- 2. KIỂM TRA SỐ LƯỢNG VÀ TỔNG QUAN
-- ----------------------------------------------------------
-- Đếm tổng số lượng comment ở cả 3 lớp
SELECT 'Bronze' as Layer, count(*) as total FROM lakehouse.bronze_youtube_comments
UNION ALL
SELECT 'Silver' as Layer, count(*) as total FROM lakehouse.silver_youtube_comments
UNION ALL
SELECT 'Gold' as Layer, count(*) as total FROM lakehouse.gold_youtube_comment_metrics;

-- Xem 10 comment mới nhất vừa mới được đổ vào lớp Bronze
SELECT comment_id, author, text_display, ingested_at 
FROM lakehouse.bronze_youtube_comments 
ORDER BY ingested_at DESC LIMIT 10;


-- 3. KIỂM TRA KẾT QUẢ PHÂN TÍCH CẢM XÚC (INSIGHTS)
-- ----------------------------------------------------------
-- Thống kê phân phối cảm xúc
SELECT sentiment, count(*) as count, round(count(*) * 100 / sum(count(*)) over(), 2) as percentage
FROM lakehouse.silver_youtube_comments
GROUP BY sentiment;

-- Xem mẫu các bình luận TIÊU CỰC
SELECT author, text_clean 
FROM lakehouse.silver_youtube_comments 
WHERE sentiment = 'negative' LIMIT 10;

-- Tìm tác giả đóng góp tích cực nhất
SELECT author, count(*) as positive_count 
FROM lakehouse.silver_youtube_comments 
WHERE sentiment = 'positive' 
GROUP BY author 
ORDER BY positive_count DESC LIMIT 5;


-- 4. MINH CHỨNG SỨC MẠNH DELTA LAKE
-- ----------------------------------------------------------
-- Xem lịch sử các phiên bản (Time Travel)
DESCRIBE HISTORY lakehouse.silver_youtube_comments;

-- Kiểm thử khả năng UPDATE (ACID)
-- UPDATE lakehouse.silver_youtube_comments SET sentiment = 'positive' WHERE comment_id = 'ABC';


-- 5. TRUY VẤN LỚP GOLD (BUSINESS LAYER)
-- ----------------------------------------------------------
-- Xem tổng hợp metric từ bảng Gold chính
SELECT * FROM lakehouse.gold_youtube_comment_metrics;

-- Xem phân rã cảm xúc theo video
SELECT video_id, sentiment, total_comments 
FROM lakehouse.gold_youtube_sentiment_breakdown 
ORDER BY total_comments DESC;


-- 6. KIỂM TRA CHẤT LƯỢNG (DQ CHECK)
-- ----------------------------------------------------------
-- Kiểm tra comment bị lặp (Duplicate ID)
SELECT comment_id, count(*) FROM lakehouse.silver_youtube_comments GROUP BY comment_id HAVING count(*) > 1;

-- Thống kê thảo luận theo giờ
SELECT hour(ingested_at) as hour, count(*) as count FROM lakehouse.silver_youtube_comments GROUP BY hour ORDER BY hour;
