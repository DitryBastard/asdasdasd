import { LANGUAGES } from '../languages'

export default function LanguageSelector({
  value,
  onChange,
}: {
  value: string
  onChange: (value: string) => void
}) {
  return (
    <select className="lang-select" value={value} onChange={(e) => onChange(e.target.value)}>
      {LANGUAGES.map((lang) => (
        <option key={lang.code} value={lang.code}>
          {lang.label}
        </option>
      ))}
    </select>
  )
}
