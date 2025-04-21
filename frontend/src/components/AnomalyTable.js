import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  flexRender,
} from '@tanstack/react-table';

function AnomalyTable({ tableData = [], anomalyData = [], showOnlyAnomalies }) {
  const anomalyIds = useMemo(() => {
    return new Set(anomalyData.map(anomaly => anomaly.id));
  }, [anomalyData]);

  const displayData = useMemo(() => {
    if (showOnlyAnomalies) {
      return tableData.filter(row => anomalyIds.has(row.id));
    } else {
      return tableData;
    }
  }, [tableData, anomalyIds, showOnlyAnomalies]);

  const columns = useMemo(
    () => [
        { header: 'Port Name', accessorKey: 'port_name', id: 'port_name', width: '10%' },
        { header: 'State', accessorKey: 'state', id: 'state', width: '10%', cell: info => <div style={{ textAlign: 'center' }}>{info.getValue()}</div> },
        { header: 'Border', accessorKey: 'border', id: 'border', width: '10%', cell: info => <div style={{ textAlign: 'center' }}>{info.getValue()}</div> },
        {
            header: 'Date',
            accessorKey: 'date',
            id: 'date',
            width: '10%', 
            cell: info => {
                const dateStr = info.getValue(); 
                if (!dateStr) return ''; 

                try {
                    const dateObj = new Date(dateStr + 'T00:00:00Z');

                    return dateObj.toLocaleDateString(undefined, {
                        month: 'short',
                        year: 'numeric',
                        timeZone: 'UTC'
                    });
                } catch (e) {
                    console.error("Error formatting date:", dateStr, e);
                    return dateStr;
                }
            }
        },
        { header: 'Measure', accessorKey: 'measure', id: 'measure', width: '15%' },
        {
            header: 'Value',
            accessorKey: 'value',
            id: 'value',
            width: '5%',
            cell: info => {
                const value = info.getValue();
                const formattedValue = (value !== null && value !== undefined)
                ? parseInt(value, 10).toLocaleString()
                : 'N/A';
                return ( <div style={{ textAlign: 'right', paddingRight: '10px', fontWeight: 'bold' }}> {formattedValue} </div> );
            },
        },
        { header: 'Latitude', accessorKey: 'latitude', id: 'latitude', width: '5%', cell: info => info.getValue()?.toFixed(3) },
        { header: 'Longitude', accessorKey: 'longitude', id: 'longitude', width: '5%', cell: info => info.getValue()?.toFixed(3) },
        {
            header: 'Anomaly Info',
            accessorFn: row => anomalyData.find(a => a.id === row.id)?.anomaly_reason || '',
            id: 'anomaly_info',
            width: '30%',
            cell: info => <span style={{ color: 'red', fontSize: '0.9em' }}>{info.getValue()}</span>
        }
    ],
    [anomalyData] // Dep
  );

  const table = useReactTable({
    data: displayData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 25 } },
    debugTable: process.env.NODE_ENV === 'development',
  });

  const hasDisplayData = displayData && displayData.length > 0;

  return (
    <div style={{ margin: '20px 0' }}>
      <h2>Data Table</h2>
      {!hasDisplayData && <p>(No data matches the current filters{showOnlyAnomalies ? ' and anomaly criteria' : ''})</p>}
      {hasDisplayData && (
        <>
         <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #ccc', tableLayout: 'fixed' }}>
            <thead>
                {table.getHeaderGroups().map(headerGroup => (
                <tr key={headerGroup.id} style={{ backgroundColor: '#f2f2f2' }}>
                    {headerGroup.headers.map(header => (
                    <th
                      key={header.id}
                      style={{
                        width: header.column.columnDef.width,
                        border: '1px solid #ddd',
                        padding: '10px 8px',
                        textAlign: 'left',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                        {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                    </th>
                    ))}
                </tr>
                ))}
            </thead>
            <tbody>
                {table.getRowModel().rows.map(row => {
                  const isAnomaly = anomalyIds.has(row.original.id);
                  const anomalyReason = anomalyData.find(a => a.id === row.original.id)?.anomaly_reason || (isAnomaly ? 'Detected as anomaly' : '');
                  return (
                      <tr
                        key={row.id}
                        style={{ backgroundColor: isAnomaly ? '#fff0f0' : 'white', borderBottom: '1px solid #eee' }}
                        title={anomalyReason} // full reason on hover
                      >
                      {row.getVisibleCells().map(cell => {
                          const isAnomalyCol = cell.column.id === 'anomaly_info';
                          return (
                            <td
                              key={cell.id}
                              style={{
                                border: '1px solid #ddd',
                                padding: '6px 8px',
                                verticalAlign: 'middle',
                                ...(isAnomalyCol && {
                                    overflow: 'hidden',
                                    whiteSpace: 'nowrap',
                                    textOverflow: 'ellipsis',
                                })
                              }}
                            >
                              {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </td>
                          );
                      })}
                      </tr>
                  );
                })}
            </tbody>
            </table>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', flexWrap: 'wrap', gap: '10px' }}>
            <span style={{ fontSize: '0.9em' }}> Page <strong> {table.getState().pagination.pageIndex + 1} of {table.getPageCount()} </strong> | Rows: {table.getRowModel().rows.length} of {table.getPrePaginationRowModel().rows.length} </span>
             <select value={table.getState().pagination.pageSize} onChange={e => { table.setPageSize(Number(e.target.value)) }} style={{ padding: '5px' }} > {[10, 25, 50, 100, 250].map(pageSize => ( <option key={pageSize} value={pageSize}> Show {pageSize} </option> ))} </select>
            <div> <button onClick={() => table.setPageIndex(0)} disabled={!table.getCanPreviousPage()} style={{ padding: '5px 10px', marginRight: '5px' }}> {'<< First'} </button> <button onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()} style={{ padding: '5px 10px', marginRight: '5px' }}> {'< Previous'} </button> <button onClick={() => table.nextPage()} disabled={!table.getCanNextPage()} style={{ padding: '5px 10px', marginRight: '5px' }}> {'Next >'} </button> <button onClick={() => table.setPageIndex(table.getPageCount() - 1)} disabled={!table.getCanNextPage()} style={{ padding: '5px 10px' }}> {'Last >>'} </button> </div>
          </div>
        </>
      )}
    </div>
  );
}

export default AnomalyTable;
