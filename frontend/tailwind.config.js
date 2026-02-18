/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      spacing: {
        '1': '8px',
        '2': '16px',
        '3': '24px',
        '4': '32px',
        '6': '48px',
        '8': '64px',
      },
      fontSize: {
        'sm': ['14px', '20px'],
        'base': ['16px', '24px'],
        'lg': ['18px', '28px'],
        'xl': ['20px', '28px'],
        '2xl': ['24px', '32px'],
        '3xl': ['30px', '36px'],
      },
      colors: {
        'bg': '#FFFFFF',
        'bg-secondary': '#F8F9FA',
        'border': '#E5E7EB',
        'text': '#111827',
        'text-secondary': '#6B7280',
        'primary': '#2563EB',
        'primary-hover': '#1D4ED8',
        'success': '#059669',
        'error': '#DC2626',
      },
      borderRadius: {
        DEFAULT: '8px',
      },
      boxShadow: {
        'sm': '0 1px 2px rgba(0,0,0,0.05)',
        'md': '0 4px 6px rgba(0,0,0,0.07)',
      },
      transitionTimingFunction: {
        'base': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      transitionDuration: {
        'base': '150ms',
      },
    },
  },
  plugins: [],
}
