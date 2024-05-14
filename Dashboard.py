import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from requests.auth import HTTPBasicAuth
import numpy as np
st.set_page_config(
    page_title="Sagawa DMS Dashboard",
    page_icon="📊",
    layout="wide"
    )


# URLs for the data
urls = {
    "documents": "http://sagawa.epik.live/api/v4/documents/",
    "cabinets": "http://sagawa.epik.live/api/v4/cabinets/",
    "tags": "http://sagawa.epik.live/api/v4/tags/",
    "groups": "http://sagawa.epik.live/api/v4/groups/",
    "metadata_types": "http://sagawa.epik.live/api/v4/metadata_types/"
}

# Basic Authentication
auth = HTTPBasicAuth('admin', 'JzWnZGWASr2Qnf@cM8jT')

# Function to fetch data from an API

def fetch_data(endpoint_url):
    all_data = []
    while endpoint_url:
        response = requests.get(endpoint_url, auth=auth)
        if response.status_code == 200:
            data = response.json()
            all_data.extend(data['results'])
            endpoint_url = data['next']
        else:
            st.error(f"Failed to fetch data from {endpoint_url}: Status {response.status_code}")
            break
    return all_data

# Sidebar for selecting the view
option = st.sidebar.selectbox(
    "Select Dashboard View",
    ("Document Type",  "Cabinet Document Distribution", "Document Tags", "Document Count by Index and Node Value")
)


# Main dashboard layout based on sidebar selection
# Depending on the option, display appropriate visuals
if option == "Document Type":
    st.header('Document Types')
    df_documents = pd.DataFrame(fetch_data(urls['documents']))
    df_documents['type_label'] = df_documents['document_type'].apply(lambda x: x.get('label') if isinstance(x, dict) else None)
    unique_document_types_count = df_documents['type_label'].nunique()
    if not df_documents.empty:
        # Document Type Charts
        # [Include your visualization code for Document Types here]
        col1, col2, col3 = st.columns([1.5, 4, 4.5], gap='small')
        total_documents_count = df_documents.shape[0]
# Tính toán tổng số loại tài liệu (loại tài liệu duy nhất)
        
        with col1:
            st.markdown('##### Statistics')
            st.metric(label="Total Documents", value=f"{total_documents_count}")
            st.metric(label="Total Document Types", value=f"{unique_document_types_count}")
        with col2:
            
            st.markdown('##### Document Type Distribution')
            type_counts = df_documents['type_label'].value_counts().reset_index()
            type_counts.columns = ['type_label', 'count']
            fig_pie = px.pie(type_counts, names='type_label', values='count', width=400)
            st.plotly_chart(fig_pie)
        with col3:
            st.markdown('##### Popularity of Document Types by Label')
            # Determine min and max values for input based on data
            min_doc_count = type_counts['count'].min()
            max_doc_count = type_counts['count'].max()
            # Filter input
            col_number_input1, col_number_input2, col_number_input_empty = st.columns([ 3, 3,4], gap='small')
            with col_number_input1:
                min_count = st.number_input('Minimum count', min_value=0, max_value=max_doc_count, value=min_doc_count)
            with col_number_input2:
                max_count = st.number_input('Maximum count', min_value=0, max_value=max_doc_count, value=max_doc_count)
            # Filtering based on input
            filtered_type_counts = type_counts[(type_counts['count'] >= min_count) & (type_counts['count'] <= max_count)]
            fig_bubble = px.scatter(filtered_type_counts, x='type_label', y='count',
                                size='count', color='type_label',
                                hover_name='type_label', size_max=40, width=450)
            st.plotly_chart(fig_bubble)

        
        st.markdown('##### Bar Chart of Document Types')
        fig_bar = px.bar(type_counts, x='count', y='type_label', color='type_label',
                     labels={'type_label': 'Document Type', 'count': 'Count'},
                      text='count', width=1000,height=450)
        fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig_bar)


        col1, col2 = st.columns([6, 4], gap="medium")
        with col1:
            st.markdown('##### Document File Extensions')
            df_documents['file_extension'] = df_documents['file_latest'].apply(lambda x: x['mimetype'].split('/')[-1].upper() if isinstance(x, dict) else None)

            # Count the frequency of each file extension
            extension_counts = df_documents['file_extension'].value_counts().reset_index()
            extension_counts.columns = ['File Extension', 'Count']

            # Create a Bar Chart
            fig_file_extension = px.bar(extension_counts, x='File Extension', y='Count', color='File Extension',
                                     text='Count', width=600)
            fig_file_extension.update_traces(texttemplate='%{text}', textposition='outside')
            fig_file_extension.update_layout(bargap=0.5)
            st.plotly_chart(fig_file_extension)

        with col2:
            st.markdown('##### Top documents')

            # Fetch data from the "documents" API
            df_documents = pd.DataFrame(fetch_data(urls['documents']))

            # Calculate document type counts based on the 'label' key
            type_counts = df_documents['document_type'].apply(lambda x: x.get('label') if isinstance(x, dict) else None).value_counts().reset_index()
            type_counts.columns = ['Document Type', 'Count']

            # Sort and filter top documents
            top_documents_df = type_counts.sort_values(by='Count', ascending=False).head(10)

            # Check if DataFrame is empty before calculating max_count
            if not top_documents_df.empty:
                max_count = top_documents_df['Count'].max()
            else:
                max_count = 0  # Or any default value for an empty DataFrame

            # Use st.data_editor to display the table with document type labels
            st.data_editor(
                top_documents_df,
                column_order=("Document Type", "Count"),
                column_config={
                    "Document Type": st.column_config.TextColumn(
                        "Document Types",  # Set the header text as "Document Types"
                    ),
                    "Count": st.column_config.ProgressColumn(
                        "Number of Documents",
                        format="%f",  # Display format for count
                        min_value=float(0),
                        max_value=float(max_count),
                    ),
                },
                hide_index=True,  # Hide the index column
            )
        
    st.header('Document Growth Over Time')
    df_documents = pd.DataFrame(fetch_data(urls['documents']))
    if not df_documents.empty:
            #Document Growth Over Time:
        # Convert datetime_created to datetime and extract date part
        df_documents['date'] = pd.to_datetime(df_documents['datetime_created']).dt.date
        df_documents['document_type'] = df_documents['document_type'].apply(lambda x: x.get('label') if isinstance(x, dict) else None)
        df_documents['file_extension'] = df_documents['file_latest'].apply(lambda x: x['mimetype'].split('/')[-1].upper() if isinstance(x, dict) else None)

        # Determine the earliest and latest dates in the dataset
        min_date = df_documents['date'].min()
        max_date = df_documents['date'].max()

        
        
        col1, col2 = st.columns([4,6])
        with col2:
            # User input for date range and view selection in the same column
            col_start_date, col_end_date,col_empty_date = st.columns([3,3,4])
            with col_start_date:
                start_date = st.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date)
            with col_end_date:
                end_date = st.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)
            option = st.selectbox('Choose Data View', ['Document Types Growth Over Time', 'File Extension Growth Over Time'])

            # Filtering data based on date range
            filtered_documents = df_documents[(df_documents['date'] >= start_date) & (df_documents['date'] <= end_date)]

            # Function to prepare data for plotting
            def prepare_data(df, group_field):
                df_grouped = df.groupby(['date', group_field]).size().reset_index(name='count')
                df_pivot = df_grouped.pivot(index='date', columns=group_field, values='count').fillna(0).cumsum().reset_index()
                return df_pivot

            # Choose data view and plot
            if option == 'Document Types Growth Over Time':
                df_plot = prepare_data(filtered_documents, 'document_type')
                title = "Document Type Growth Over Time"
            else:
                df_plot = prepare_data(filtered_documents, 'file_extension')
                title = "File Extension Growth Over Time"

            # Plotting
            if not df_plot.empty:
                fig = px.line(df_plot, x='date', y=[col for col in df_plot.columns if col != 'date'],
                            labels={'value': 'Number of Documents', 'date': 'Date'},
                            title=title, height=400)
                fig.update_layout(xaxis_title='Date', yaxis_title='Cumulative Document Count', legend_title=option[:-16])
                st.plotly_chart(fig)
            else:
                st.write("No data to display for the selected range.")

        with col1:
            # Display document details in a table
            st.write("Filtered Documents:", filtered_documents[['label', 'document_type']])

       
           
            






elif option == "Cabinet Document Distribution":
    st.header('Cabinets')
    df_cabinets = pd.DataFrame(fetch_data(urls['cabinets']))
    if not df_cabinets.empty:
        def fetch_data(endpoint_url):
            all_data = []
            while endpoint_url:
                response = requests.get(endpoint_url, auth=auth)
                if response.status_code == 200:
                    data = response.json()
                    all_data.extend(data['results'])
                    endpoint_url = data['next']
                else:
                    st.error(f"Failed to fetch data from {endpoint_url}: Status {response.status_code}")
                    break
            return all_data

        # Function to fetch direct document count for a cabinet
        def fetch_direct_document_count(documents_url):
            response = requests.get(documents_url, auth=auth)
            if response.status_code == 200:
                documents = response.json()
                return documents['count']
            else:
                st.error(f"Failed to fetch documents from {documents_url}: Status {response.status_code}")
                return 0

        # Load data from APIs
        df_cabinets = pd.DataFrame(fetch_data(urls['cabinets']))

        # Prepare cabinet data with direct document counts
        if not df_cabinets.empty:
            
            cabinet_data = []
            for index, row in df_cabinets.iterrows():
                document_count = fetch_direct_document_count(row['documents_url'])  # Fetch direct documents only
                full_path = row['full_path'].split(' / ')
                if len(full_path) > 1:
                    parent_name = full_path[-2]  # Gets the second last element as parent for children
                else:
                    parent_name = "All Cabinets"  # Default parent for top-level cabinets

                cabinet_data.append({
                    'parent': parent_name,
                    'label': row['label'],
                    'document_count': document_count
                })

            df_cabinet_documents = pd.DataFrame(cabinet_data)

            # Treemap with document counts
            fig_cabinets = px.treemap(df_cabinet_documents, path=[px.Constant("All Cabinets"), 'parent', 'label'], values='document_count',
                                    title="Cabinet Document Distribution", hover_data={'label': True, 'document_count': True}, height=600, width=900)
            st.plotly_chart(fig_cabinets)
        # Cabinet Document Distribution Charts
        # [Include your Treemap visualization here]

elif option == "Document Tags":
    st.header('Document Tags')
    df_tags = pd.DataFrame(fetch_data(urls['tags']))
    if not df_tags.empty:
        # Document Tags Charts
                # Function to fetch document count for each tag
        def fetch_tag_documents(url):
            response = requests.get(url, auth=auth)
            if response.status_code == 200:
                data = response.json()
                return data['count']
            else:
                return 0  # Or handle errors appropriately

        # Load data from APIs
        df_tags = pd.DataFrame(fetch_data(urls['tags']))

        if not df_tags.empty:
            
            # Add document count to each tag
            df_tags['document_count'] = df_tags['documents_url'].apply(fetch_tag_documents)
            df_tags['color'] = df_tags.apply(lambda x: x['color'], axis=1)

            # Bar Chart for Tags
            fig_tags = px.bar(df_tags, x='label', y='document_count', title="Documents by Tag",height=600, width=900,
                            color='color', text='document_count')
            fig_tags.update_layout(showlegend=False)  # Optional: Turn off the legend if color coding is sufficient
            st.plotly_chart(fig_tags)
        # [Include your Tags Bar Chart visualization here]
        

elif option == "Document Count by Index and Node Value":
    st.header('Document Count by Index and Node Value')
    # Fetch index data and process each index
    # [Include your Stacked Bar Chart visualization here]
    index_url = "http://sagawa.epik.live/api/v4/index_instances/"
    auth = HTTPBasicAuth('admin', 'JzWnZGWASr2Qnf@cM8jT')

    # Function to fetch all data from an API
    def fetch_all_data(endpoint_url):
        all_data = []
        while endpoint_url:
            response = requests.get(endpoint_url, auth=auth)
            if response.status_code == 200:
                data = response.json()
                all_data.extend(data['results'])
                endpoint_url = data['next']
            else:
                st.error(f"Failed to fetch data from {endpoint_url}: Status {response.status_code}")
                break
        return all_data

    # Recursive function to fetch documents for nodes and sub-nodes
    def fetch_documents(node_url):
        nodes = fetch_all_data(node_url)
        node_documents = []
        for node in nodes:
            documents = fetch_all_data(node['documents_url'])
            document_count = len(documents)
            node_documents.append({
                'Node Value': node['value'],
                'Document Count': document_count
            })
            # Recursively fetch for child nodes
            if node.get('children_url'):
                node_documents.extend(fetch_documents(node['children_url']))
        return node_documents

    # Fetch index data and process each index
    node_counts = []
    for index in fetch_all_data(index_url):
        node_documents = fetch_documents(index['nodes_url'])
        for node_doc in node_documents:
            node_counts.append({
                'Index Label': index['label'],
                'Node Value': node_doc['Node Value'],
                'Document Count': node_doc['Document Count']
            })

    # Convert to DataFrame
    df_node_counts = pd.DataFrame(node_counts)

    # Create a stacked bar chart
    
    fig = px.bar(df_node_counts, x='Index Label', y='Document Count', color='Node Value', text='Document Count', height=600,width=900, barmode='stack')
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    st.plotly_chart(fig)