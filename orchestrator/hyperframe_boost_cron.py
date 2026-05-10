import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)

if __name__ == "__main__":
    from orchestrator.hyperframe_boost_agent import HyperframeBoostAgent
    try:
        HyperframeBoostAgent().run()
    except Exception as e:
        logging.getLogger(__name__).error("HyperFrame Boost cron crashed: %s", e, exc_info=True)
        sys.exit(1)
