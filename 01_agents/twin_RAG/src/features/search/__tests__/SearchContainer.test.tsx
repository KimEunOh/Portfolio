import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SearchContainer } from '@/features/search/components/SearchContainer';
import http from '@/remote/http';

jest.mock('@/remote/http', () => ({
  __esModule: true,
  default: { get: jest.fn() },
}));

function wrapper(children: React.ReactNode) {
  const qc = new QueryClient();
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('SearchContainer', () => {
  it('shows empty state then renders results', async () => {
    (http.get as jest.Mock).mockResolvedValue({ data: { items: [{ id: '1', title: 'Test' }] } });

    const user = userEvent.setup();
    render(wrapper(<SearchContainer />));

    // empty
    expect(await screen.findByText('검색 결과가 없습니다.')).toBeInTheDocument();

    const input = screen.getByPlaceholderText('검색어를 입력하세요');
    await user.type(input, 'bank');
    await user.click(screen.getByRole('button', { name: /검색/i }));

    expect(await screen.findByText('Test')).toBeInTheDocument();
  });
});


