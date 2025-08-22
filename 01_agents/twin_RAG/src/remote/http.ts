'use client';

import axios from 'axios';

// Axios 인스턴스: 기본값은 현재 오리진(`/`) 기준, 환경변수로 백엔드 게이트웨이를 지정 가능
const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

export const httpClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  // 타임아웃은 보수적으로 설정
  timeout: 15000,
});

export default httpClient;


