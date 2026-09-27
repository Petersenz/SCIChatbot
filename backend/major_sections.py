"""Read major-owned sections without inferring ownership from source websites."""
import re

def section(description, heading):
    blocks = re.split(r'(?m)^##\s+(.+?)\s*$', description or '')
    found = [blocks[i+1].strip() for i in range(1,len(blocks)-1,2) if blocks[i].strip()==heading]
    return found[0] if len(found)==1 else ''

def owned_sources(plan, majors):
    if not plan or not plan.major_names or plan.route not in ('staff','contact'):
        return None
    selected = [m for m in majors if m.major_name_th in plan.major_names]
    result=[]
    for major in selected:
        if plan.route=='staff':
            content=section(getattr(major,'description',''),'บุคลากร')
        else:
            fields=(('โทรศัพท์','tel'),('อีเมล','email'),('เว็บไซต์','website_url'),('Facebook','facebook_page'))
            content='\n'.join(f'{label}: {getattr(major,key)}' for label,key in fields if getattr(major,key,None))
            address=section(getattr(major,'description',''),'ติดต่อ')
            if address: content += '\n'+address
        if content:
            result.append(dict(title=major.major_name_th+' — '+('บุคลากร' if plan.route=='staff' else 'ติดต่อ'),url=f'/records/majors/{major.id}',text=major.major_name_th+'\n'+content))
    return result or None
