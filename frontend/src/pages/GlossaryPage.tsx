import { useState } from 'react'
import GlossaryForm from '../components/GlossaryForm'
import GlossaryList from '../components/GlossaryList'

export default function GlossaryPage() {
  const [refreshKey, setRefreshKey] = useState(0)
  const bump = () => setRefreshKey((k) => k + 1)

  return (
    <div className="memory-page">
      <div className="glossary-form-row">
        <GlossaryForm onAdded={bump} />
      </div>
      <GlossaryList refreshKey={refreshKey} />
    </div>
  )
}
