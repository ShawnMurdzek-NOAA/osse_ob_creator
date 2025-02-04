# osse\_ob\_creator Example

In this example, vertical profiles from 3 UAS sites will be created using `osse_ob_creator`. These UAS observations will then be combined with conventional obs, superobbed, and saved to a prepBUFR file.

This example should work "out-of-the-box" on Orion.

### Steps

1. `mkdir osse_ob_creator_EXAMPLE`
2. `cd osse_ob_creator_EXAMPLE`
3. `git clone https://github.com/ShawnMurdzek-NOAA/osse_ob_creator.git`
4. `cd osse_ob_creator`
5. `cp example/synthetic_ob_creator_param.yml .`
6. Edit `synthetic_ob_creator_param.yml`:
    1. Change `/path/to/osse_ob_creator_EXAMPLE` to your `osse_ob_creator_EXAMPLE` path (this appears in several places, including outside of the `paths` section.
    2. Change `user` to your username
7. Activate your Python environment
8. Create bash jobs: `python create_syn_ob_jobs.py synthetic_ob_creator_param.yml`
9. Submit bash jobs: `bash cron_run_synthetic_ob_creator.sh`
