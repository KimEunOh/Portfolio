require('@testing-library/jest-dom');

const React = require('react');
jest.mock('next/image', () => {
  return function MockImage(props) {
    return React.createElement('img', { ...props });
  };
});


