/***************************************************************************
*   (c) Jürgen Riegel (juergen.riegel@web.de) 2014                        *
*                                                                         *
*   This file is part of the FreeCAD CAx development system.              *
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU Library General Public License (LGPL)   *
*   as published by the Free Software Foundation; either version 2 of     *
*   the License, or (at your option) any later version.                   *
*   for detail see the LICENCE text file.                                 *
*                                                                         *
*   FreeCAD is distributed in the hope that it will be useful,            *
*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
*   GNU Library General Public License for more details.                  *
*                                                                         *
*   You should have received a copy of the GNU Library General Public     *
*   License along with FreeCAD; if not, write to the Free Software        *
*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
*   USA                                                                   *
*                                                                         *
*   Juergen Riegel 2014                                                   *
***************************************************************************/

#include "PreCompiled.h"

#ifndef _PreComp_

#endif

#include <Base/Console.h>
#include "ActiveObjectList.h"
#include <Gui/Application.h>
#include <Gui/Document.h>
#include <Gui/Selection.h>
#include <Gui/ViewProviderDocumentObject.h>

FC_LOG_LEVEL_INIT("MDIView",true,true);

using namespace Gui;

App::DocumentObject *ActiveObjectList::getObject(const ObjectInfo &info, bool resolve,
        App::DocumentObject **parent, std::string *subname) const
{
    if(parent) *parent = info.obj;
    if(subname) *subname = info.subname;
    auto obj = info.obj;
    if(!obj || !obj->getNameInDocument())
        return 0;
    if(info.subname.size()) {
        obj = obj->getSubObject(info.subname.c_str());
        if(!obj)
            return 0;
    }
    return resolve?obj->getLinkedObject(true):obj;
}

void ActiveObjectList::setHighlight(const ObjectInfo &info, HighlightMode mode, bool enable) {
    auto obj = getObject(info,false);
    if(!obj) return;
    auto vp = dynamic_cast<ViewProviderDocumentObject*>(Application::Instance->getViewProvider(obj));
    if(vp)
        vp->getDocument()->signalHighlightObject(*vp, mode, enable);
}

Gui::ActiveObjectList::ObjectInfo Gui::ActiveObjectList::getObjectInfo(
        App::DocumentObject *obj, const char *subname) const 
{
    ObjectInfo info;
    info.obj = 0;
    if(!obj || !obj->getNameInDocument())
        return info;
    if(subname || obj->getDocument()==_Doc->getDocument()) {
        info.obj = obj;
        if(subname) info.subname = subname;
    }else{
        // If the input object is not from this document, it must be brought in
        // by some link type object of this document. We only accept the object
        // if we can find such object in the current selection.
        auto sels = Gui::Selection().getSelection(_Doc->getDocument()->getName(),false);
        for(auto &sel : sels) {
            const char *sub = sel.SubName;
            const char *dot = sub;
            for(auto sobj=sel.pObject;dot;sub=dot,dot=strchr(sub,'.')) {
                if(dot!=sel.SubName) {
                    sobj = sobj->getSubObject(std::string(sub,dot-sub+1).c_str());
                    if(!sobj) break;
                }
                if(sobj == obj || sobj->getLinkedObject() == obj) {
                    info.obj = sel.pObject;
                    if(dot!=sel.SubName)
                        info.subname = std::string(sel.SubName,dot-sel.SubName+1);
                    if(subname) info.subname += subname;
                    break;
                }
            }
            if(info.obj) break;
        }
    }
    return info;
}

bool Gui::ActiveObjectList::hasObject(App::DocumentObject *obj, 
        const char *name, const char *subname) const
{
    auto it = _ObjectMap.find(name);
    if(it==_ObjectMap.end())
        return false;
    auto info = getObjectInfo(obj,subname);
    return info.obj==it->second.obj && info.subname==it->second.subname;
}

void Gui::ActiveObjectList::setObject(App::DocumentObject* obj, const char* name, 
        const char *subname, const Gui::HighlightMode& mode)
{
    auto it = _ObjectMap.find(name);
    if(it!=_ObjectMap.end()) {
        setHighlight(it->second,mode,false);
        _ObjectMap.erase(it);
    }
    if(!obj) return;

    auto info = getObjectInfo(obj,subname);
    if(!info.obj) {
        FC_ERR("Cannot set active object " << obj->getDocument()->getName() << '.' 
                << obj->getNameInDocument() << '.' << (subname?subname:"") 
                << " in document '" << _Doc->getDocument()->getName() 
                << "'. Not found in current selection");
        return;
    }

    _ObjectMap[name] = info;
    setHighlight(info,mode,true);
}

bool Gui::ActiveObjectList::hasObject(const char*name)const 
{
    return _ObjectMap.find(name) != _ObjectMap.end();
}

void ActiveObjectList::objectDeleted(const ViewProviderDocumentObject &vp)
{
  //maybe boost::bimap or boost::multi_index
  for (auto it = _ObjectMap.begin(); it != _ObjectMap.end(); ++it)
  {
    if (it->second.obj == vp.getObject())
    {
      _ObjectMap.erase(it);
      return;
    }
  }
}
