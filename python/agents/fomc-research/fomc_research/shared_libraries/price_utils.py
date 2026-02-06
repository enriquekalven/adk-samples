from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'Price-related utility functions for FOMC Research Agent.'
import datetime
import logging
import math
import os
from collections.abc import Sequence
from absl import app
from google.cloud import bigquery
bqclient = bigquery.Client()
logger = logging.getLogger(__name__)
MAX_ARGS = 2
MOVE_SIZE_BP = 25
DATASET_NAME = os.getenv('GOOGLE_CLOUD_BQ_DATASET', 'fomc_research_agent')
TIMESERIES_CODES = os.getenv('GOOGLE_GENAI_FOMC_AGENT_TIMESERIES_CODES', 'SFRH5,SFRZ5')

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def fetch_prices_from_bq(timeseries_codes: list[str], dates: list[datetime.date]) -> dict[dict[datetime.date, float]]:
    """Fetches prices from Bigquery.

    Args:
      timeseries_codes: List of timeseries codes to fetch.
      dates: List of dates to fetch.

    Returns:
      Dictionary of timeseries codes to dictionaries of dates to prices.
    """
    logger.debug('fetch_prices_from_bq: timeseries_codes: %s', timeseries_codes)
    logger.debug('fetch_prices_from_bq: dates: %s', dates)
    query = f'\nSELECT DISTINCT timeseries_code, date, value\nFROM {DATASET_NAME}.timeseries_data\nWHERE timeseries_code IN UNNEST(@timeseries_codes)\n  AND date IN UNNEST(@dates)\n'
    job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ArrayQueryParameter('timeseries_codes', 'STRING', timeseries_codes), bigquery.ArrayQueryParameter('dates', 'DATE', dates)])
    prices = {}
    query_job = bqclient.query(query, job_config=job_config)
    results = query_job.result()
    for row in results:
        logger.debug('code: %s, date: %s, value: %s', row.timeseries_code, row.date, row.value)
        if row.timeseries_code not in prices:
            prices[row.timeseries_code] = {row.date: row.value}
        else:
            prices[row.timeseries_code][row.date] = row.value
    return prices

def number_of_moves(front_ff_future_px: float, back_ff_future_px: float) -> float:
    """Computes the expected number of rate moves between two prices.

    Args:
      front_ff_future_px: Front fed funds future price.
      back_ff_future_px: Back fed funds future price.

    Returns:
      Number of moves.

    For calculation details see
    https://www.biancoresearch.com/bianco/samples/SR2v1.pdf

    """
    move_size_pct = MOVE_SIZE_BP / 100
    front_implied_rate = 100 - front_ff_future_px
    back_implied_rate = 100 - back_ff_future_px
    rate_delta = back_implied_rate - front_implied_rate
    num_moves = rate_delta / move_size_pct
    return num_moves

def fed_meeting_probabilities(nmoves: float) -> dict:
    move_text = 'hike' if nmoves > 0 else 'cut'
    if nmoves > 1:
        move_text = move_text + 's'
    max_expected_moves = math.ceil(abs(nmoves))
    max_expected_move_bp = max_expected_moves * MOVE_SIZE_BP
    move_odds = round(math.modf(abs(nmoves))[0], 2)
    output = {f'odds of {max_expected_move_bp}bp {move_text}': move_odds, f'odds of no {move_text}': round(1 - move_odds, 2)}
    return output

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def compute_probabilities(meeting_date_str: str) -> dict:
    """Computes the probabilities of a rate move for a specific date.

    Args:
      meeting_date_str: Date of the Fed meeting.

    Returns:
      Dictionary of probabilities.
    """
    meeting_date = datetime.date.fromisoformat(meeting_date_str)
    meeting_date_day_before = meeting_date - datetime.timedelta(days=1)
    timeseries_codes = [x.strip() for x in TIMESERIES_CODES.split(',')]
    prices = fetch_prices_from_bq(timeseries_codes, [meeting_date, meeting_date_day_before])
    error = None
    for code in timeseries_codes:
        if code not in prices:
            error = f'No data for {code}'
            break
        elif meeting_date not in prices[code]:
            error = f'No data for {code} on {meeting_date}'
            break
        elif meeting_date_day_before not in prices[code]:
            error = f'No data for {code} on {meeting_date_day_before}'
            break
    logger.debug('compute_probabilities: found prices: %s', prices)
    if error:
        return {'status': 'ERROR', 'message': error}
    near_code = timeseries_codes[0]
    far_code = timeseries_codes[1]
    num_moves_post = number_of_moves(prices[near_code][meeting_date], prices[far_code][meeting_date])
    num_moves_pre = number_of_moves(prices[near_code][meeting_date_day_before], prices[far_code][meeting_date_day_before])
    probs_pre = fed_meeting_probabilities(num_moves_pre)
    probs_post = fed_meeting_probabilities(num_moves_post)
    output = {('Odds of a rate move within the next year ', '(computed before Fed meeting):'): probs_pre, ('Odds of a rate move within the next year ', '(computed after Fed meeting)'): probs_post}
    return {'status': 'OK', 'output': output}

def main(argv: Sequence[str]) -> None:
    if len(argv) > MAX_ARGS:
        raise app.UsageError('Too many command-line arguments.')
    meeting_date = argv[1]
    print('meeting_date: ', meeting_date)
    print(compute_probabilities(meeting_date))
if __name__ == '__main__':
    app.run(main)