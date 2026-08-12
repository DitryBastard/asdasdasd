import { useState } from 'react'
import ManualEntryForm from '../components/ManualEntryForm'
import MemoryList from '../components/MemoryList'
import MemoryUpload from '../components/MemoryUpload'

export default function MemoryPage() {
  const [refreshKey, setRefreshKey] = useState(0)
  const bump = () => setRefreshKey((k) => k + 1)

  return (
    <div className="memory-page">
      <div className="memory-forms">
        <MemoryUpload onCommitted={bump} />
        <ManualEntryForm onAdded={bump} />
      </div>
      <MemoryList refreshKey={refreshKey} />
    </div>
  )
}
