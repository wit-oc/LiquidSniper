ALTER TABLE sr_zones ADD COLUMN carry_score REAL;
ALTER TABLE sr_zones ADD COLUMN body_respect_score REAL;
ALTER TABLE sr_zones ADD COLUMN close_inside_rate REAL;
ALTER TABLE sr_zones ADD COLUMN body_overlap_rate REAL;
ALTER TABLE sr_zones ADD COLUMN wick_only_rate REAL;
ALTER TABLE sr_zones ADD COLUMN directional_close_rate REAL;
ALTER TABLE sr_zones ADD COLUMN counter_close_rate REAL;
