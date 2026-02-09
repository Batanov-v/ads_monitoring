import unittest

from ads_monitoring.fetcher import FIELDS, count_pairs, offers_to_rows, parse_offers


SAMPLE_HTML = """
<html>
  <body>
    <table>
      <tr><th>Not</th><th>Relevant</th></tr>
      <tr><td>foo</td><td>bar</td></tr>
    </table>
    <table>
      <tr>
        <th>Offer ID</th>
        <th>Сайт</th>
        <th>Домен</th>
        <th>Категория</th>
        <th>Продажа</th>
        <th>Условия</th>
        <th>Motivation Amount</th>
        <th>Offer Duration, days</th>
        <th>Юридическое лицо</th>
        <th>Green Probability</th>
      </tr>
      <tr>
        <td>123</td>
        <td>example</td>
        <td>example.com</td>
        <td>Retail</td>
        <td>10%</td>
        <td>Online</td>
        <td>500</td>
        <td>30</td>
        <td>ООО Ромашка</td>
        <td>90%</td>
      </tr>
      <tr>
        <td>124</td>
        <td>example</td>
        <td>example.com</td>
        <td>Retail</td>
        <td>10%</td>
        <td>Offline</td>
        <td>600</td>
        <td>45</td>
        <td>ООО Ромашка</td>
        <td>80%</td>
      </tr>
    </table>
  </body>
</html>
"""


class FetcherTests(unittest.TestCase):
    def test_parse_offers_with_flexible_headers(self) -> None:
        offers = parse_offers(SAMPLE_HTML)
        self.assertEqual(len(offers), 2)
        self.assertEqual(offers[0]["id"], "123")
        self.assertEqual(offers[0]["offerDuration"], "30")
        self.assertEqual(offers[0]["legalName"], "ООО Ромашка")

    def test_count_pairs_and_rows(self) -> None:
        offers = parse_offers(SAMPLE_HTML)
        counts = count_pairs(offers)
        self.assertEqual(counts[("example.com", "10%")], 2)
        rows = offers_to_rows(offers)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], [offers[0][field] for field in FIELDS])


if __name__ == "__main__":
    unittest.main()
