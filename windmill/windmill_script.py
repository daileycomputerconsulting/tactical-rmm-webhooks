from wmill import task, task_script, step, sleep, wait_for_approval, get_resume_urls, workflow, get_variable
import hmac
import hashlib
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IMPORTANT: All computation must happen inside @task(), task_script(), or step().
# Code outside these wrappers is NOT checkpointed and WILL be re-executed
# on every resume or retry. Never put API calls, database writes, or
# non-deterministic logic (e.g. datetime.now()) in the top-level workflow body.

# task_script() references a module file (see the helper.py tab)
github_data_worker = task_script("./github_data_worker.py")
trmm_data_worker = task_script("./tacticalrmm_data_worker.py")

# @task() wraps a function as a workflow step that runs as a separate job.
# The result is checkpointed — on retry, completed tasks are skipped.
@task()
async def process(body: str, header_signature: str) -> str:
    secret = get_variable("GITHUB_WEBHOOK_SECRET")

    if header_signature is None:
        logger.error("failed sig validation")
        return False

    sha_type, signature = header_signature.split("=")
    if sha_type != "sha256":
        logger.error("failed sig validation - invalid hash algorithm")
        return False
    
    hash_object = hmac.new(secret.encode('utf-8'), msg=body.encode('utf-8'), digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, header_signature):
        logger.error("failed sig validation")
        return False
    logger.info("validated sig!")
    return True


@workflow
async def main(body: dict, x_hub_signature_256: str, x_github_event: str,raw_string: str):
    a = await process(raw_string, x_hub_signature_256)

    #logger.info(json.dumps(body, indent=4))

    if not body:
        logger.error("invalid body")
        return {}
    
    logger.info("getting scripts from github repo")
    github_scripts = await github_data_worker(payload=body, event=x_github_event)
    logger.info("finished getting scripts from github repo")

    result_status = trmm_data_worker(github_scripts=github_scripts)
    # task_script() calls a module file as a separate job (also checkpointed)
    # b = await helper(a=a)

    # step() runs inline code and checkpoints the result (no child job).
    # Use it for lightweight operations you don't want as a separate script.
    # urls = await step("get_urls", lambda: get_resume_urls())

    # sleep() suspends the workflow server-side without holding a worker
    # await sleep(1)

    # wait_for_approval() suspends until an external event resumes it.
    # Like sleep(), it does not hold a worker. Approve/reject URLs are
    # available in the timeline step's details in the UI.
    # approval = True # await wait_for_approval(timeout=3600)

    return {
        "result status": "good" if result_status else "fail"
    }
