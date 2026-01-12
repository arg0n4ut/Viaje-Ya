import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '1m',
};

const BASE = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const res = http.get(`${BASE}/`);
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}
