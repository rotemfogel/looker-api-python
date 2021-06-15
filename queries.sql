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

SELECT g.name, u.name
  FROM looker_groups g
  LEFT JOIN looker_user_groups ug
    ON (    ug.group_id = g.id
        AND g.id NOT IN (1,12,10))
  LEFT JOIN looker_users u
    ON (ug.user_id = u.id)
 ORDER BY g.id, u.id;