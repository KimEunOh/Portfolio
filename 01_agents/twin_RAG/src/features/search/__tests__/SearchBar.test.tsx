import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SearchBar } from '@/features/search/components/SearchBar';

describe('SearchBar', () => {
  it('renders input and triggers submit on enter', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    const handleSubmit = jest.fn();

    render(<SearchBar query="" onQueryChange={handleChange} onSubmit={handleSubmit} />);

    const input = screen.getByPlaceholderText('검색어를 입력하세요');
    await user.type(input, 'visa{enter}');

    expect(handleChange).toHaveBeenCalled();
    expect(handleSubmit).toHaveBeenCalledTimes(1);
  });
});


