-- users query
SELECT id, name, user_roles, is_disabled, last_login
  FROM (SELECT u.id, u.name, group_concat(g.name) user_roles, is_disabled, last_login
          FROM looker_users u
          LEFT JOIN looker_user_groups ug
            ON (ug.user_id = u.id)
          LEFT JOIN looker_groups g
            ON (    ug.group_id = g.id
                AND g.id NOT IN (1,12,10))
         GROUP BY 1,2,4
         ORDER BY u.id) a
 WHERE user_roles IS NOT NULL;

-- groups query
SELECT g.name group_name, u.name user_name
  FROM looker_users u
  JOIN looker_user_groups ug
    ON (ug.user_id = u.id)
  JOIN looker_groups g
    ON (    ug.group_id = g.id
        AND g.id NOT IN (1,10,11,12,13))
 WHERE u.id > 1
 ORDER BY g.name, u.id;

-- find multiple groups
WITH d AS (
  SELECT u.id, u.name, group_concat(g.name) user_roles, is_disabled, last_login
    FROM looker_users u
    LEFT JOIN looker_user_groups ug
      ON (ug.user_id = u.id)
    LEFT JOIN looker_groups g
      ON (    ug.group_id = g.id
          AND g.id NOT IN (1,10,11,12,13))
   WHERE u.id > 1
   GROUP BY 1,2,4,5
  HAVING COUNT(g.name)>1
)
SELECT *
  FROM d
 ORDER BY id;

-- find multiple roles
WITH d AS (
  SELECT u.id, u.name, group_concat(r.name) user_roles, is_disabled, last_login
    FROM looker_users u
    LEFT JOIN looker_user_roles ur
      ON (ur.user_id = u.id)
    LEFT JOIN looker_roles r
      ON (ur.role_id = r.id)
   WHERE u.id > 1
  --   AND NOT is_disabled
   GROUP BY 1,2,4,5
  HAVING COUNT(r.name)>1
)
SELECT *
  FROM d
 WHERE user_roles IS NOT NULL
 ORDER BY id;