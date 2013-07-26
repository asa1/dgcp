SELECT *
FROM (
        SELECT relativePath,id FROM Albums WHERE id IN ( 
                        SELECT album FROM Images WHERE id IN (
                                SELECT imageid FROM ImageTags WHERE tagid=61
                        )
                )
        ) tag61

INNER JOIN (
        SELECT id FROM Albums WHERE id IN (
                        SELECT album FROM Images WHERE id IN (
                                SELECT imageid FROM ImageTags WHERE tagid=5
                        )
                )
) tag5
ON tag61.id=tag5.id
INNER JOIN (
        SELECT id FROM Albums WHERE id IN (
                        SELECT album FROM Images WHERE id IN (
                                SELECT imageid FROM ImageTags WHERE tagid=6
                        )
                )
) tag6
ON tag5.id=tag6.id
INNER JOIN (
	SELECT id FROM Albums WHERE id IN (
		SELECT album FROM Images WHERE id IN (
			SELECT imageid FROM ImageInformation WHERE rating>3 AND rating<5
		)
	)
) rating
ON tag6.id=rating.id
;
