.headers on
.mode column
PRAGMA index_list('compatibility');
SELECT a,b,COUNT(*) AS cnt
FROM compatibility
GROUP BY a,b
HAVING COUNT(*) > 1;
