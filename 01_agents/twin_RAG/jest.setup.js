require('@testing-library/jest-dom');
require('whatwg-fetch');

const React = require('react');
jest.mock('next/image', () => {
  return function MockImage(props) {
    return React.createElement('img', { ...props });
  };
});


