SELECT id, name, user_roles, last_login,
       last_login_year,
       concat(last_login_year,'-', 
              CASE
                WHEN last_login_month < 10 
                  THEN concat('0', last_login_month) 
                  ELSE last_login_month 
              END) last_login_month
  FROM (SELECT u.id, u.name, group_concat(g.name) user_roles, last_login,
               YEAR(last_login) last_login_year,
               MONTH(last_login) last_login_month
          FROM looker_users u
          LEFT JOIN looker_user_groups ug
            ON (ug.user_id = u.id)
          LEFT JOIN looker_groups g
            ON (    ug.group_id = g.id
                AND g.id NOT IN (1,12,10))
         GROUP BY 1,2,4,5
         ORDER BY u.id) a;

SELECT u.id, u.name, group_concat(g.name) user_roles, is_disabled, last_login
  FROM looker_users u
  LEFT JOIN looker_user_groups ug
    ON (ug.user_id = u.id)
  LEFT JOIN looker_groups g
    ON (    ug.group_id = g.id
        AND g.id NOT IN (1,12,10))
 WHERE u.id > 1
 GROUP BY 1,2,4,5
 ORDER BY u.id;

WITH admins AS (
  SELECT g.name group_name, u.name user_name
    FROM looker_groups g
    JOIN looker_user_groups ug
      ON (    ug.group_id = g.id
          AND g.id = 3)
    JOIN looker_users u
      ON (ug.user_id = u.id)
   WHERE NOT u.is_disabled
),
lg AS (
  SELECT MAX(ug.group_id) group_id , u.id
    FROM looker_user_groups ug
    LEFT JOIN looker_users u
      ON (ug.user_id = u.id)
   WHERE NOT u.is_disabled
     AND ug.group_id IN (7,8,9)
  GROUP BY u.id
)
SELECT g.name group_name, u.name user_name
  FROM looker_groups g
  JOIN lg
    ON (lg.group_id = g.id)
  JOIN looker_users u
    ON (lg.id = u.id)
 WHERE NOT u.is_disabled
 UNION ALL 
 SELECT group_name, user_name
   FROM admins
 ORDER BY 1;

WITH users AS (
  SELECT DISTINCT u.name email, datediff(current_date(), u.last_login) days_since_last_login
    FROM looker_user_groups ug
    JOIN looker_users u
      ON (ug.user_id = u.id AND ug.group_id IN (8,9))
   WHERE NOT u.is_disabled
     AND u.name like '%seekingalpha%'
)
SELECT email, days_since_last_login
  FROM users
 WHERE days_since_last_login > 90
 ORDER BY 2 DESC;
 
 
WITH users AS (
  SELECT DISTINCT u.name email, datediff(current_date(), u.last_login) days_since_last_login
    FROM looker_user_groups ug
    JOIN looker_users u
      ON (ug.user_id = u.id AND ug.group_id = 7)
   WHERE NOT u.is_disabled
     AND u.name like '%seekingalpha%'
)
SELECT email, days_since_last_login
  FROM users
 WHERE days_since_last_login > 90
 ORDER BY 2 DESC;